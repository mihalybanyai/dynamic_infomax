# Notebooks

**What this is.** Transcriptions of MB's paper notebooks, one file per page, each with the
action items distilled from it. A transcription is Claude's draft until MB marks it
checked. [handwriting.md](handwriting.md) is what Claude has learned about reading MB's
hand.

*Drafted by Claude on 2026-11-10; layout and scan policy set by MB the same day.*

## Procedure

1. Read [handwriting.md](handwriting.md) before transcribing.
2. Transcribe verbatim and mark every doubt (see *Markup*); never smooth a doubtful word
   into a plausible one.
3. Draft action items by topic (e.g. *Empirics*, *Theory*), each linked to the repo files
   it bears on. MB edits them. Claude's suggestions sit under the item they serve,
   marked *Claude:*, with epistemic tags.
4. MB resolves the doubts. Fix the page, and add each misreading and each confirmed
   letter form to handwriting.md, so the next page starts from it.
5. When MB has read the page, set *Checked* below and delete the scan.

**Action items stay on the page.** Notebook threads are too raw even for
`notes/parked_ideas.md`: nothing moves to `notes/`, `empirics/` or `specs/` unless MB
explicitly decides it. Claude may mark a suggestion `**Route?**` with a target where
moving it would be especially useful; MB trawls the pages now and then
(`grep -rn 'Route?' resources/notebooks`).

**Initials stay initials.** When MB says in chat who an initial stands for, that is
context for the chat only; the repo keeps the initial.

Once a few notebooks are done, extract this into `skills/transcribe-notebook.md`.

## Files and scans

A page is `<date written>-<occasion or topic>.md`, e.g. `2026-11-09-meeting-fj.md`; its
header names the occasion. Scans are not committed (`.gitignore`): a scan stays beside
its page only until MB has checked the transcription.

## Markup

- Text in the language written. Accents restored where the word is unambiguous; spelling
  otherwise kept.
- `{word?}` uncertain reading; `{a|b?}` competing readings; `{?}` illegible.
  `grep -rn '?}' resources/notebooks` lists what is still open.
- `~~text~~` struck out on the page. Doodles and illegible struck-out words are left out.
- `*[…]*` a non-text mark (arrow, box) described.
- `— *en: …*` Claude's English gloss of a Hungarian line. The gloss also shows how Claude
  read the line, so a wrong gloss exposes a misreading.
- Nesting follows the indentation of the dashes; `---` is a rule drawn on the page.

## Pages

| File | Written | Occasion | Topics | Checked |
|---|---|---|---|---|
| [2026-11-09-meeting-fj](2026-11-09-meeting-fj.md) | 2026-11-09 | meeting with FJ | pre-training that teaches a likelihood; causality across context switches; hyperpriors over spec 002's natures | yes |
