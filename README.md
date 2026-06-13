# AGET-Bench — Instruction-Density Ladder (public slice)

A slice of AGET-Bench: does an LLM's compliance with explicit coding rules degrade as the
number of presented rules rises? Built on **Claude Build Day, 2026-06-13**, orchestrated via
the AGET governed workflow (gated plan + rubric the run is scored against).

## Built on Build Day vs vendored prior work
| Path | Origin | Status |
|------|--------|--------|
| `original/` | authored 2026-06-13 | Build Day contribution |
| `vendor/` | poc/vocab-spec-compliance (Feb 2026) | prior work, headered; included only so the slice runs standalone |

`original/` = the density-ladder methodology (subsetting a fixed-mix rule corpus), the
isolated-sandbox runner, the presented-vs-unpresented density-aware scorer, the clean
pre-registration, and the opus-4.8 results produced 2026-06-13.

## Findings & limits (honest)
- Shipped conditions: **d05: 16 scoreable + 4 prose-only (n=20) | d10: 20 scoreable + 0 prose-only (n=20) | d20: 20 scoreable + 0 prose-only (n=20)**. ("prose-only" = the subject answered in prose with no extractable
  code block; the scorer excludes these from the pass-rate denominator and reports the count.)
- **Result — presented-rule compliance is density-invariant** (scored 2026-06-13 via
  `score_density_ladder.py`; PRESENTED strict %, Wilson 95% CI):

  | density | n | PRESENTED strict % [95% CI] |
  |--------:|--:|-----------------------------|
  | d05 (5 rules)  | 16 | 80.0 [70.0, 87.3] |
  | d10 (10 rules) | 20 | 75.0 [68.6, 80.5] |
  | d20 (20 rules) | 20 | 75.8 [71.3, 79.7] |

  All three CIs overlap across a 4x range in rule count — compliance does **not** fall as more rules
  are presented (P2 FLAT). Consistent with prior in-house findings (rules add little marginal signal
  at this density); this is a *density-invariance* result, not a novel completeness claim.
- **d30 (30 rules): results NOT shipped** — only n=1 run completed (the run stopped before d30); a
  single observation is not reportable. The d30 *variant definition* (`variants/density/d30.md`) IS
  included for reproducibility — it is simply the full 30-rule corpus, regenerable from
  `vendor/corpus_30_rules.md` via `build_density_variants.py` (no held-out content).
- N up to 20 per cell, single subject (opus-4.8). Absolute pass-rates are scorer-heuristic-dependent;
  the relative (across-density) comparison is the valid read.

## What this slice does and does NOT show (honest)
Compliance here is **behavioral, not self-reported**: the scorer runs a deterministic rule-checker
(`vendor/score_g2.score_rules`) against the model's code — pass/fail is computed, never parsed from
the model's prose claim.
- **Shows**: density-invariance of presented-rule compliance (CIs overlap across d05/d10), and honest
  handling of degenerate (prose-only) runs.
- **Does NOT show**: a self-verify/retry loop or a "model claimed pass, executor caught it, model
  retried" moment. This is **single-shot** generate-then-score; there is no retry here.
- A *separate* AGET-Bench arm (NOT shipped in this slice) is where text-keyed scoring was found to
  false-positive on honest refusals — that result is why this benchmark trusts executed signals over
  model self-reports, but it is not demonstrated by the d05/d10 data here.

## Run
```
python3 original/build_density_variants.py     # regenerate variants from vendor/corpus_30_rules.md
bash    original/run_density.sh                 # opus x {d05,d10,d20,d30} x N=20 (API-billed; isolated sandboxes)
python3 original/score_density_ladder.py        # presented vs unpresented strict %, Wilson 95% CI
```

## Release hygiene
This is a vetted public slice of a larger, ongoing internal benchmark. Held-out evaluation cells,
internal calibration data, and pre-registration design for unreleased arms are excluded by
construction. The slice was assembled by surgical allowlist into a fresh tree (no prior git history)
and scanned for credentials and unreleased material before publication.

## License
Apache-2.0 (matching the AGET framework).
