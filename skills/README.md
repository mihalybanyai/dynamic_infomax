# skills/

Each file in this directory is a procedural skill that Claude should follow
when the relevant task comes up. Claude Code reads `AGENTS.md` first, then
loads skills from here as needed.

## Current skills

- `write-math-spec.md` — turning an idea into a specification in `specs/`
- `derive-test-suite.md` — going from spec to test suite before code
- `document-experiment.md` — structuring an entry in `experiments/`

## Adding a new skill

A skill is a markdown file with:

1. A clear name (kebab-case, .md extension)
2. A one-sentence description at the top (used for matching)
3. The procedure itself, written for Claude to follow

Skills should be discovered, not designed: when you find yourself repeating
the same instruction across sessions, extract it into a skill.
