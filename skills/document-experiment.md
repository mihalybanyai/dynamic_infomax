# Skill: document-experiment

> Use this skill when starting or completing an experiment in `experiments/`.

## Goal

Every experiment is a directory containing enough information that a
labmate (or future you) can:

1. Understand what question the experiment was trying to answer
2. Reproduce the run
3. Read the results without re-running the code

## Procedure for starting an experiment

1. **Create the directory.** `experiments/NNN-short-name/`, sequence number
   continuing from existing experiments.

2. **Write a `PLAN.md`** with:

   - **Question** — one sentence. What are we trying to learn?
   - **Hypothesis** — what we expect to see, and why.
   - **Method** — pointers to specs/code involved, plus the experimental
     setup (hyperparameters, datasets, seeds).
   - **Success criteria** — how will we know if the hypothesis is supported?
   - **Failure modes to watch for** — what could go wrong and silently
     produce a misleading result?

3. **Set up the directory:**
   ```
   experiments/NNN-short-name/
   ├── PLAN.md
   ├── run.py            # or run.sh — the entry point
   ├── config.yaml       # or .toml — the configuration
   ├── output/           # gitignored
   └── README.md         # written after the experiment, see below
   ```

## Procedure for completing an experiment

After the experiment is run, write a `README.md` in the experiment directory:

- **Result** — one paragraph. What happened.
- **Figures** — embed or link the key plots.
- **Interpretation** — does this support the hypothesis? What does it mean?
- **What I'd do differently** — for the next iteration.
- **Provenance** — git commit hash, date, hardware, runtime.

## Output

A new `experiments/NNN-short-name/` directory with `PLAN.md` initially, then
`README.md` and results after the run.
