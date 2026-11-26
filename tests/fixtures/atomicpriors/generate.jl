# Spec 002 §5.5: AtomicPriors.jl reference fixtures for T12 (tests/test_002_references.py).
#
# Run from the repository root, on exactly one thread (DD-J1):
#
#     julia --threads=1 --project=tests/fixtures/atomicpriors tests/fixtures/atomicpriors/generate.jl [fixtures...]
#
# With no arguments every fixture is written; arguments pick some: ymap pstar capacity mutual
# transtrum pstar_highD. This folder's environment pins AtomicPriors.jl to its upstream commit and
# LineSearches below 7.5 (DD-J1). Each JSON file holds values and metadata only: T12's
# tolerances are fixed by spec §5.5 and pinned in tests/spec002_common.py.
# Design decisions DD-J1 to DD-J3 are in docs/002-foreign-q-prediction/README.md.

Threads.nthreads() == 1 && Threads.maxthreadid() == 1 || error(
    "run with `julia --threads=1`: AtomicPriors sizes its per-thread buffers by nthreads(), " *
    "and since Julia 1.12 an interactive thread lets threadid() exceed it (DD-J1)")

using AtomicPriors, ForwardDiff, JSON, LinearAlgebra, Pkg, Printf, Random, Statistics

const HERE = @__DIR__
const SIGMA = 0.1                                   # §5.5: every fixture at sigma = 0.1
const TIMES = collect(range(1.0, 5.0; length=26))   # A&M's 26 times in [1, 5] (spec §4.1)
const SEEDS = (20261125, 20261126)                  # two seeds, for each estimate's spread
const CAP = 700.0                                   # transtrum's log-rate cap (DD-J2)

const AP_COMMIT = let
    info = Pkg.dependencies()[Base.UUID("6350a65c-1f9f-411a-8f08-5b635ea788f0")]
    something(info.git_revision, "unknown")
end

# ---------------------------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------------------------

"""Every number in a fixture must be finite: a NaN or Inf is an error here, never a value."""
check_finite(x::Number, path) = isfinite(x) || error("non-finite value $x at $path")
check_finite(x::AbstractString, path) = nothing
check_finite(x::Nothing, path) = nothing
check_finite(x::AbstractDict, path) = foreach(((k, v),) -> check_finite(v, "$path.$k"), x)
check_finite(x::Union{AbstractVector,Tuple}, path) = foreach(((i, v),) -> check_finite(v, "$path[$i]"), enumerate(x))

function write_fixture(name::String, fx::Dict)
    check_finite(fx, name)
    path = joinpath(HERE, name * ".json")
    open(io -> JSON.print(io, fx, 1), path, "w")
    @printf("wrote %s\n", relpath(path))
end

"""The metadata T12 asserts before it compares values (§5.5)."""
meta(; D, N=1, extra...) = Dict{String,Any}(
    "atomicpriors_commit" => AP_COMMIT, "julia_version" => string(VERSION),
    "seed" => collect(SEEDS), "sigma" => SIGMA, "D" => D, "N" => N, "coordinates" => "xi",
    "times" => TIMES, "spread" => Dict{String,Any}(), (string(k) => v for (k, v) in extra)...)

rows(M::AbstractMatrix) = [collect(c) for c in eachcol(M)]     # D x k columns -> k rows of D
sorted_rows(M::AbstractMatrix) = [sort(collect(c)) for c in eachcol(M)]

# In the compact coordinate the map is A&M's y_t(xi) = mean_mu xi_mu^t, this spec's xi (§5.5).
ycompact(xi::AbstractMatrix) = AtomicPriors.yexp_compact(xi, TIMES)
ycompact(xi::AbstractVector) = yexp(xi, TIMES; compact=true)

"""States on the ordered `Theta` in `xi`: a grid of step `1/n`, faces included."""
function ordered_grid(D::Int, n::Int)
    levels = range(0.0, 1.0; length=n + 1)
    pts = [collect(c) for c in Iterators.product(ntuple(_ -> levels, D)...) if issorted(c)]
    reduce(hcat, pts)
end

# ---------------------------------------------------------------------------------------------
# (a) ymap: y(xi) and the metric at 10 states on the ordered Theta, D = 3
# ---------------------------------------------------------------------------------------------

function fixture_ymap()
    D, n = 3, 10
    rng = Xoshiro(SEEDS[1])
    xi = sort(rand(rng, D, n); dims=1)            # sorted uniforms: uniform on the ordered box
    y = [ycompact(c) for c in eachcol(xi)]
    fim = map(eachcol(xi)) do c
        J = ForwardDiff.jacobian(ycompact, collect(c))
        rows(J' * J / SIGMA^2)                   # (1.2.1) at sigma_eff = sigma (N = 1)
    end
    fx = meta(D=D, n_states=n, xi=rows(xi), y=y, fim=fim,
              method="yexp(xi, times; compact=true); metric J'J / sigma^2 with J from ForwardDiff")
    write_fixture("ymap", fx)
end

# ---------------------------------------------------------------------------------------------
# (b) pstar: p*'s atoms and weights, I_{p*} and B(p*), D in {2, 3}, N = 1
# ---------------------------------------------------------------------------------------------

const PSTAR_START = 200        # starting atoms for nlopt!, about 3x the optimum's (DD-J3)
const NLOPT_FTOL = 1e-8        # nlopt!'s absolute stopping tolerance on ekern, in nats (DD-J3)
const MERGE_RADIUS = 0.1       # atoms closer than this in prediction space, in units of sigma
const I_DRAWS = 1_000_000      # mcarlo draws for I, in total over the atoms
const B_GRID = Dict(2 => 50, 3 => 20)  # B's states: ordered grid of step 1/n in xi
const B_SCREEN = 2_000         # fcarlo draws per state, first stage
const B_TOP = 20               # states re-estimated in the second stage
const B_FINE = 200_000         # fcarlo draws per state, second stage

"""Merge atoms whose predictions lie within `MERGE_RADIUS * sigma` (single linkage), at their
weighted mean in `xi`; nlopt!'s own `unique` merges only up to 5 digits (DD-J3). Each atom is
first sorted onto the ordered `Theta`: `y` is symmetric in the rates, so `nlopt!` returns
permuted copies of one atom, such as `(0.97, 0)` and `(0, 0.97)`, whose unsorted mean
`(0.48, 0.48)` would be a different atom."""
function merge_atoms(xi::AbstractMatrix, w::AbstractVector; sigma=SIGMA)
    xi = sort(xi; dims=1)
    y = ycompact(xi)
    k = size(xi, 2)
    label = collect(1:k)
    find(i) = label[i] == i ? i : (label[i] = find(label[i]))
    for a in 1:k, b in 1:a-1
        norm(y[:, a] - y[:, b]) < MERGE_RADIUS * sigma && (label[find(a)] = find(b))
    end
    groups = unique(find.(1:k))
    W = [sum(w[find.(1:k) .== g]) for g in groups]
    X = reduce(hcat, [sum(xi[:, find.(1:k) .== g] .* w[find.(1:k) .== g]', dims=2) / W[j]
                      for (j, g) in enumerate(groups)])
    X, W, k - length(groups)
end

"""Bias pressure's worst case `B = max_theta f_KL(theta) - I` over an ordered grid, faces
included, in two stages so that noise in the screening estimates does not inflate the
maximum (as the eye test does, spec §5.3)."""
function worst_bias_pressure(xi, w, D, I, rng)
    states = ordered_grid(D, B_GRID[D])
    ystates, yatoms = ycompact(states), ycompact(xi)
    Random.seed!(rng)
    f1 = fcarlo(ystates, yatoms, w, SIGMA, B_SCREEN * size(states, 2))
    top = partialsortperm(f1, 1:B_TOP; rev=true)
    f2 = fcarlo(ystates[:, top], yatoms, w, SIGMA, B_FINE * B_TOP)
    i = argmax(f2)
    f2[i] - I, states[:, top[i]], size(states, 2)
end

function fixture_pstar(D::Int)
    t = @elapsed p = nlopt!(q -> ekern(yexp(q, TIMES), SIGMA * sqrt(2)), sobol(D, PSTAR_START); ftol=NLOPT_FTOL)
    xi, w, merged = merge_atoms(p.array, p.weights)
    est = map(SEEDS) do s
        Random.seed!(s)
        I = mcarlo(ycompact(xi), w, SIGMA, I_DRAWS)
        B, argB, n_states = worst_bias_pressure(xi, w, D, I, s)
        (; I, B, argB, n_states)
    end
    I, B = mean(e.I for e in est), mean(e.B for e in est)
    @printf("p* D = %d: %d atoms (%d merged) in %.0f s, I = %.4f nats, B = %.4f nats\n",
            D, length(w), merged, t, I, B)
    fx = meta(D=D, atoms=sorted_rows(xi), weights=w, I=I, B=B,
              B_argmax=sort(est[1].argB), B_states=est[1].n_states,
              n_start=PSTAR_START, merged=merged, merge_radius_sigma=MERGE_RADIUS,
              method="nlopt!(ekern(yexp(p, times), sigma*sqrt(2)); ftol=$NLOPT_FTOL) from sobol(D, $PSTAR_START); " *
                     "I by mcarlo ($I_DRAWS draws), B by fcarlo on an ordered grid; mean of two seeds")
    fx["spread"] = Dict("I" => abs(est[1].I - est[2].I), "B" => abs(est[1].B - est[2].B))
    write_fixture("pstar_D$D", fx)
end

# ---------------------------------------------------------------------------------------------
# (f) pstar_highD: I_{p*} at A&M's D in {5, 7}, N = 1, the reference for the atomic path
# ---------------------------------------------------------------------------------------------

const HIGHD_START = 100        # about twice the 54-57 atoms the optimum keeps (2026-11-26)

function fixture_pstar_highD(D::Int)
    t = @elapsed p = nlopt!(q -> ekern(yexp(q, TIMES), SIGMA * sqrt(2)), sobol(D, HIGHD_START); ftol=NLOPT_FTOL)
    xi, w, merged = merge_atoms(p.array, p.weights)
    Is = map(SEEDS) do s
        Random.seed!(s)
        mcarlo(ycompact(xi), w, SIGMA, I_DRAWS)
    end
    @printf("p* D = %d: %d atoms (%d merged) in %.0f s, I = %.4f nats (seeds differ by %.4f)\n",
            D, length(w), merged, t, mean(Is), abs(Is[1] - Is[2]))
    fx = meta(D=D, atoms=sorted_rows(xi), weights=w, I=mean(Is), n_start=HIGHD_START, merged=merged,
              merge_radius_sigma=MERGE_RADIUS,
              method="nlopt!(ekern(yexp(p, times), sigma*sqrt(2)); ftol=$NLOPT_FTOL) from sobol(D, $HIGHD_START); " *
                     "I by mcarlo ($I_DRAWS draws); mean of two seeds. A kernel-bound optimum: a floor for I_{p*}, not its value")
    fx["spread"] = Dict("I" => abs(Is[1] - Is[2]))
    write_fixture("pstar_D$D", fx)
end

# ---------------------------------------------------------------------------------------------
# (c) capacity: C_N at sigma_eff = sigma / sqrt(N), N in {2, 4}, D = 2
# ---------------------------------------------------------------------------------------------

# §5.5(c) as first written used `repeat`, which builds the N-fold channel of a discrete-outcome
# likelihood and cannot run on 26-dimensional Gaussian data. It now runs (b)'s recipe at the
# reduced noise: an external check of the capacity solver where p* has more atoms (MB,
# 2026-11-25). The atoms grow like N^(D/2), so the start does too (about 1.5x, DD-J3).
const CAPACITY_START = Dict(2 => 200, 4 => 400)
const C_DRAWS = 2_000_000

function fixture_capacity(N::Int)
    D, s_eff = 2, SIGMA / sqrt(N)
    t = @elapsed p = nlopt!(q -> ekern(yexp(q, TIMES), s_eff * sqrt(2)), sobol(D, CAPACITY_START[N]); ftol=NLOPT_FTOL)
    xi, w, merged = merge_atoms(p.array, p.weights; sigma=s_eff)
    Cs = map(SEEDS) do s
        Random.seed!(s)
        mcarlo(ycompact(xi), w, s_eff, C_DRAWS)
    end
    @printf("C_N, N = %d: %d atoms (%d merged) in %.0f s, C = %.4f nats (seeds differ by %.4f)\n",
            N, length(w), merged, t, mean(Cs), abs(Cs[1] - Cs[2]))
    fx = meta(D=D, N=N, sigma_eff=s_eff, C_N=mean(Cs), atoms=sorted_rows(xi), weights=w,
              n_start=CAPACITY_START[N], merged=merged, merge_radius_sigma=MERGE_RADIUS,
              method="nlopt!(ekern(yexp(p, times), sigma_eff*sqrt(2)); ftol=$NLOPT_FTOL) from sobol(D, $(CAPACITY_START[N])); " *
                     "C_N by mcarlo at sigma_eff ($C_DRAWS draws); mean of two seeds")
    fx["spread"] = Dict("C_N" => abs(Cs[1] - Cs[2]))
    write_fixture("capacity_N$N", fx)
end

# ---------------------------------------------------------------------------------------------
# (d) mutual: I of a fixed prior, the 15 ordered points of {0.1, ..., 0.9}^2, equal weights
# ---------------------------------------------------------------------------------------------

const MUTUAL_DRAWS = 4_000_000

function fixture_mutual()
    levels = (0.1, 0.3, 0.5, 0.7, 0.9)
    atoms = [[a, b] for a in levels for b in levels if a <= b]   # T12(d)'s order
    xi = reduce(hcat, atoms)
    w = fill(1 / length(atoms), length(atoms))
    Is = map(SEEDS) do s
        Random.seed!(s)
        mcarlo(ycompact(xi), w, SIGMA, MUTUAL_DRAWS)
    end
    @printf("fixed prior: I = %.5f nats (seeds differ by %.5f)\n", mean(Is), abs(Is[1] - Is[2]))
    fx = meta(D=2, atoms=atoms, weights=w, I=mean(Is),
              method="mcarlo(yexp(prior, times), sigma, $MUTUAL_DRAWS); mean of two seeds")
    fx["spread"] = Dict("I" => abs(Is[1] - Is[2]))
    write_fixture("mutual_fixed", fx)
end

# ---------------------------------------------------------------------------------------------
# (e) transtrum: the cloud of theta-hat at D = 2, N = 1, 2000 points, sorted xi
# ---------------------------------------------------------------------------------------------

const CLOUD = 2000
const WALKERS = 200            # emcee walks in the 26-dimensional data space: at least 28
const THIN = 1600              # keep every 1600th step of each walker (DD-J3)
const EDGE = 0.02              # T12(e)'s edge width in xi

"""The exp-decay map in transtrum's unbounded log-rate coordinate, `k = exp(theta)`, with
`theta` capped at `CAP` (DD-J2): for `theta >= log(746) ~ 6.6` both `y` and its derivative are
already exactly 0 in Float64 (t >= 1), and only above `log(floatmax) ~ 709.78` does `exp`
overflow, making the derivative `-t Inf 0 = NaN`. Below the cap every value is unchanged bit
for bit; above it the NaN becomes its limit, 0. Any other NaN still raises an error."""
ylograte(theta::AbstractVector) = yexp(min.(theta, CAP), TIMES)

xi_from_lograte(theta) = exp.(-exp.(theta))          # xi = exp(-k), k = exp(theta)

edge_fractions(z) = [mean(abs.(z[2, :] .- z[1, :]) .< EDGE), mean(z[1, :] .< EDGE), mean(z[2, :] .> 1 - EDGE)]

const REFIT_STARTS = 3         # transtrum's own fit plus two random log-rates

"""Re-fit one data point tightly (spec 002 §5.5(e), DD-J3): LsqFit with x_tol = g_tol = 1e-15
from transtrum's own estimate and from random log-rates, keeping the smallest residual.
transtrum's fits stop early along flat ridges, which moved its coinciding-rates fraction
by about 0.03 (2026-11-26)."""
function tight_refit(x::AbstractVector, theta0::AbstractVector, rng)
    J = similar(x, length(x), length(theta0))
    f(_, th) = ylograte(th)
    jac(_, th) = ForwardDiff.jacobian!(J, ylograte, th)
    best, cost = theta0, sum(abs2, ylograte(theta0) .- x)
    for k in 1:REFIT_STARTS
        start = k == 1 ? theta0 : randn(rng, length(theta0))
        fit = AtomicPriors.LsqFit.curve_fit(f, jac, 1:0, x, start; x_tol=1e-15, g_tol=1e-15, maxIter=5000)
        c = sum(abs2, fit.resid)
        if isfinite(c) && c < cost
            best, cost = fit.param, c
        end
    end
    best
end

function fixture_transtrum()
    clouds = map(SEEDS) do s
        Random.seed!(s)
        xs, _, ths = AtomicPriors._transtrum(ylograte, Weighted(randn(Xoshiro(s), 2, WALKERS)), SIGMA,
                                             (CLOUD + 200) * THIN; nthin=THIN, verbose=false)
        size(ths, 2) >= CLOUD || error("transtrum returned $(size(ths, 2)) points, fewer than $CLOUD")
        keep = sort(randperm(Xoshiro(s), size(ths, 2))[1:CLOUD])
        rng = Xoshiro(s + 1)
        refit = reduce(hcat, [tight_refit(xs[:, i], ths[:, i], rng) for i in keep])
        moved = mean(abs.(sort(xi_from_lograte(refit); dims=1) .- sort(xi_from_lograte(ths[:, keep]); dims=1)) .> 1e-3)
        @printf("seed %d: re-fit moved %.1f%% of the coordinates by more than 1e-3 in xi\n", s, 100moved)
        sort(xi_from_lograte(refit); dims=1)
    end
    e1, e2 = edge_fractions(clouds[1]), edge_fractions(clouds[2])
    se = sqrt.(max.(e1 .* (1 .- e1), 1 / CLOUD) / CLOUD .* 2)     # binomial SE of a difference
    @printf("transtrum: edge fractions %s, seeds differ by %s binomial SEs\n",
            string(round.(e1; digits=4)), string(round.(abs.(e1 .- e2) ./ se; digits=2)))
    fx = meta(D=2, cloud=CLOUD, theta_hat=rows(clouds[1]), walkers=WALKERS, thin=THIN,
              lograte_cap=CAP, edge_fractions=e1, refit_starts=REFIT_STARTS,
              method="transtrum(theta -> yexp(min.(theta, $CAP), times), walkers from randn(Xoshiro(seed), 2, $WALKERS), sigma, n; " *
                     "nthin=$THIN), $CLOUD points drawn without replacement, each re-fitted by LsqFit at x_tol = g_tol = 1e-15 " *
                     "from $REFIT_STARTS starts, mapped to sorted xi; seed 1's cloud")
    fx["spread"] = Dict("edge_coinciding" => abs(e1[1] - e2[1]), "edge_xi0" => abs(e1[2] - e2[2]),
                        "edge_xi1" => abs(e1[3] - e2[3]), "edge_in_binomial_se" => abs.(e1 .- e2) ./ se)
    write_fixture("transtrum", fx)
end

# ---------------------------------------------------------------------------------------------

const ALL = ("ymap", "pstar", "pstar_highD", "capacity", "mutual", "transtrum")

function main(args)
    which = isempty(args) ? ALL : Tuple(args)
    all(in(ALL), which) || error("unknown fixture in $which; choose from $ALL")
    @printf("AtomicPriors %s, Julia %s, seeds %s\n", AP_COMMIT[1:7], VERSION, SEEDS)
    "ymap" in which && fixture_ymap()
    "pstar" in which && foreach(fixture_pstar, (2, 3))
    "pstar_highD" in which && foreach(fixture_pstar_highD, (5, 7))
    "capacity" in which && foreach(fixture_capacity, (2, 4))
    "mutual" in which && fixture_mutual()
    "transtrum" in which && fixture_transtrum()
end

if abspath(PROGRAM_FILE) == @__FILE__   # run as a script; `include` it to reuse the pieces
    main(ARGS)
end
