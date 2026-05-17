# Passing random generators — how and why

> A project-specific tutorial on how we handle randomness in code. The
> conventions are stricter than typical Python practice, and the
> rationale matters as much as the mechanics.

## The problem we're avoiding

Most Python code that uses numpy randomness looks like this:

```python
# In some library file
def add_noise(x):
    return x + np.random.normal(0, 1, x.shape)

# In some other file
np.random.seed(42)
y = add_noise(x)
```

This *appears* reproducible: same seed, same output. But it has a silent
failure mode. The `np.random.normal()` call reads from a single global
random state, shared by every function in every imported library. If
*anything* — a new import, a logging library that uses RNG internally,
a different version of some package that calls `np.random.rand()` in
its constructor — changes the sequence of calls between `np.random.seed(42)`
and `add_noise(x)`, the output silently changes. Months later when
someone tries to reproduce the result, they get a different number.

This is not theoretical. It is one of the most common reproducibility
failures in scientific Python code.

## The fix

Don't use `np.random.*` at all in this project. Instead, pass around an
explicit `np.random.Generator` object. The same example, done right:

```python
# In some library file
def add_noise(x, rng):
    return x + rng.normal(0, 1, x.shape)

# In some other file
rng = np.random.default_rng(42)
y = add_noise(x, rng)
```

The `rng` is a self-contained object. Its state is not affected by what
any other library does. The same seed produces the same sequence of
calls from this generator, regardless of import order, regardless of
package versions, regardless of any other randomness happening
elsewhere.

## The basic patterns

### Pattern 1: function takes an rng argument

```python
def some_function(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    noise = rng.standard_normal(x.shape)
    return x + noise
```

The function does not construct an rng itself. Whoever calls it is
responsible for providing one.

### Pattern 2: the top level of an experiment constructs the rng

```python
# experiments/000-static-fig1/run.py
import numpy as np
from infomax.ba import blahut_arimoto

def main(seed: int):
    rng = np.random.default_rng(seed)
    result = blahut_arimoto(..., rng=rng)
    ...
```

One rng per experiment, constructed at the top, threaded through
everything downstream.

### Pattern 3: tests have visible hardcoded seeds

```python
def test_some_property():
    rng = np.random.default_rng(20260518)
    data = make_random_input(rng)
    ...
```

Seed is a literal number directly in the test code, not a constant
imported from elsewhere. Greppable, transparent, deterministic.

### Pattern 4: spawning independent streams

If a function needs multiple statistically-independent random streams
(e.g., one for initialisation, one for evaluation), use `rng.spawn`:

```python
rng = np.random.default_rng(seed)
init_rng, eval_rng = rng.spawn(2)

initial_state = make_init(init_rng)
evaluate_with(initial_state, eval_rng)
```

This is better than creating two separate rngs from `seed` and
`seed + 1` — `spawn` guarantees statistical independence; ad-hoc seeds
do not.

### Pattern 5: rngs in classes

```python
class BlahutArimoto:
    def __init__(self, rng: np.random.Generator, ...):
        self._rng = rng

    def step(self):
        # use self._rng inside
        ...
```

Pass at construction; store as a private attribute. Methods that need
randomness use `self._rng`.

## What you do *not* do

```python
# ✗ Forbidden: global state
np.random.normal(0, 1)
np.random.rand(10)
np.random.seed(42)

# ✗ Forbidden: constructing a generator inside library code with no seed
rng = np.random.default_rng()    # in src/

# ✗ Forbidden: hidden seeds (constants imported from elsewhere)
from project_config import TEST_SEED
rng = np.random.default_rng(TEST_SEED)   # not greppable

# ✗ Forbidden: relying on time or process state for seeding in
# experiments
seed = int(time.time())   # produces irreproducible results
```

## Where notebooks fit in

Prototyping in notebooks is the one place the rule relaxes slightly.
You don't have to thread the rng through every cell — but you should
still construct one at the top:

```python
# First cell of any notebook that uses randomness:
import numpy as np
rng = np.random.default_rng(20260518)
```

Then use `rng.random()` etc. throughout. Never use `np.random.rand()`
even in notebooks. The cost of typing `rng.` is trivial.

If a notebook produces a result that gets reported anywhere (a figure
in the report, a table in the spec), the same provenance treatment as
experiments applies — see `skills/manage-randomness.md`.

## PyTorch (for when we get there)

The same conventions apply with `torch.Generator`:

```python
def init_weights(shape, generator: torch.Generator) -> torch.Tensor:
    return torch.randn(shape, generator=generator)

# At the top of an experiment:
gen = torch.Generator(device="cpu")
gen.manual_seed(20260518)
```

`torch.manual_seed` (the global one) is only acceptable at the very top
of an experiment script, never in library code. And even there, we
prefer the explicit `torch.Generator()` pattern for consistency.

CUDA non-determinism is a separate beast not covered by this
convention; see `skills/manage-randomness.md` for what's known and
what's still v1-pending.

## Why we're strict about this

Two reasons.

**Reason 1: silent failures are the worst kind.** Code that silently
produces different results under invisible changes (a new import, a
package upgrade) is worse than code that crashes. Crashes get fixed;
silent numerical drift produces papers that don't replicate.

**Reason 2: the cost is tiny once it's a habit.** "Pass an rng" is one
extra argument. The discipline is fully transferred after about a
week of writing this way.

## External material

If you want to read more:

- **Albert Thomas, "Best Practices for Using NumPy's Random Number
  Generators"** (on the scientific-python blog):
  https://blog.scientific-python.org/numpy/numpy-rng/
  — The most thorough treatment, including parallelism and `spawn`.
- **Built In, "NumPy Random Seed: How It Works and Why to Stop Using
  It"**: https://builtin.com/data-science/numpy-random-seed
  — Good general-audience framing of the global-state problem.
- **NumPy docs, Random Generator reference**:
  https://numpy.org/doc/stable/reference/random/generator.html
  — Canonical API reference.

The Albert Thomas piece is the one to read.

## When the convention bites

There are two cases where the rule will feel onerous, and one workaround
that is *not* acceptable.

**Case 1: third-party library that calls `np.random` internally.** Some
older sklearn / scipy code reads from the global state. The fix is
usually to pass a `random_state` argument that those libraries accept
(`KMeans(random_state=42)`, etc.). If a library genuinely has no way to
take an explicit rng, document it as a known reproducibility risk in the
experiment's `README.md`.

**Case 2: deeply nested calls where threading the rng is painful.** If
you're passing rng through five layers of function calls, the API is
probably wrong — consider whether the randomness should be moved to
the top of the call chain.

**The not-acceptable workaround**: setting the global seed at the top
of an experiment as a "belt and suspenders" measure. Don't. Setting
`np.random.seed(42)` *and* using explicit rngs implies the global state
matters, which suggests it might somewhere — and means you can't trust
the explicit rng pattern. Pick one approach. We pick explicit.
