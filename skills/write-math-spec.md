# Skill: write-math-spec

> Use this skill when turning an idea or a paper concept into a formal
> specification in `specs/`, before any code is written.

## Goal

A math spec is a self-contained document that defines:

1. The objects involved (variables, spaces, distributions)
2. The relationships between them (equations, constraints)
3. The procedure or algorithm in pseudocode
4. The properties the implementation should satisfy

A spec is **framework-agnostic** — it does not commit to PyTorch vs JAX, or
to any particular tensor shape convention. It describes the math.

## Procedure

1. **Find the source.** Locate the idea — usually a file in `notes/` or
   `resources/`. If the idea exists only in conversation, write a one-page
   note in `notes/` first and link to it.

2. **Name the spec.** `specs/NNN-short-name.md`, where NNN is a zero-padded
   sequence number. Look at the existing files to pick the next number.

3. **Structure the spec with these sections, in order:**

   - **Context** — one paragraph: what problem this solves, what came before.
   - **Setup** — definitions of all symbols. Use a notation table if there are
     more than 5 symbols.
   - **Objective** — the formal objective function or property of interest.
   - **Derivation** — the math, with steps a reader can verify.
   - **Algorithm** — pseudocode. Use the convention in `skills/pseudocode-style.md`
     if it exists; otherwise use plain numbered steps with mathematical notation.
   - **Properties to verify** — what an implementation should satisfy. These
     become the test suite. Be specific: "the loss is invariant under
     permutation of the batch dimension" is good; "it should work" is not.
   - **Open questions** — anything you're unsure about. Mark with `[?]`.
   - **References** — papers, prior work. Use `[CITATION NEEDED]` if unsure.

4. **Ask before guessing.** If the source is ambiguous on a definition or
   choice, ask the human collaborator. Do not silently pick a convention.

5. **Diagram if it helps.** If the setup involves a graphical model, an
   architecture, or a data flow, produce a Mermaid or TikZ diagram in
   `diagrams/` and link to it from the spec.

## Output

A new file at `specs/NNN-short-name.md`, plus possibly a diagram. The spec
should be readable by a labmate who has not seen the source idea.
