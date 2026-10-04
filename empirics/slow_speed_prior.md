# Slow-speed prior as a co-volume gradient

*Opened 2026-10-04, from a spec 002 session collecting everyday examples of the
[co-volume](../GLOSSARY.md#co-volume) gradient; too involved for a footnote.*

A grating or texture drifting behind an aperture has the geometry of spec 002's
hypercone (§1.2): every motion and pattern parameter moves the image in proportion to
contrast, so contrast is the taper, and at zero contrast all stimuli look the same (the
tip). Low-contrast gratings are perceived as slower (Thompson 1982) [recalled]. Weiss,
Simoncelli & Adelson (2002) explain this and several aperture-problem illusions with a
Bayesian observer whose prior favours slow speeds [read: abstract].

Conjecture [guess]: part of that slow-speed preference is a co-volume gradient, not a
learned statistic of the world. For a rigidly translating pattern the Fisher metric does
not depend on speed, so Jeffreys alone is flat in speed. But if early vision low-pass
filters in time, fast motion blurs fine pattern detail, and slow motions come in more
distinguishable versions. A Jeffreys or counting observer would then favour slow speeds,
more strongly at low contrast, where the speed likelihood is broad.

*Settled by:* deriving the Fisher metric of a temporally filtered drifting-pattern model
and comparing the speed marginal of its Jeffreys prior with the speed prior Stocker &
Simoncelli (2006) inferred from psychophysics [recalled].

*Caveat:* the real-world fog version is contested. Lowering contrast uniformly lowers
perceived speed (Snowden, Stimpson & Ruddle 1998), but realistic fog, where contrast
falls with distance, raises it (Pretto, Bresciani, Rainer & Bülthoff 2012) [read:
abstracts].

- Weiss, Simoncelli & Adelson (2002). Motion illusions as optimal percepts. *Nature
  Neuroscience* 5(6), 598–604.
- Snowden, Stimpson & Ruddle (1998). Speed perception fogs up as visibility drops.
  *Nature* 392, 450.
- Pretto, Bresciani, Rainer & Bülthoff (2012). Foggy perception slows us down. *eLife*
  1, e00031.
