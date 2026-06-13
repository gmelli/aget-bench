# Pre-registration — AGET-Bench Instruction-Density Ladder (H-ABV3-001)

**Frozen**: 2026-06-13, before scoring. Scope: this density slice ONLY.

## Hypothesis
Does an LLM's compliance with PRESENTED coding rules fall as the NUMBER of presented rules rises?

## Design
- Subset a canonical 30-rule corpus at a FIXED category mix: k rules per each of 5 categories.
- Densities {5,10,20,30} = k in {1,2,4,6}. (30 is the ceiling — only 30 canonical rules exist.)
- Each variant is the ONLY AGENTS.md/CLAUDE.md the subject sees (isolated /tmp sandbox).
- Subject: claude-opus-4-8. N target = 20 per density.

## Dependent variable
- PRESENTED strict %: pass-rate over the rules the density actually gave the subject (manifest.json), Wilson 95% CI.
- UNPRESENTED strict %: pass-rate over canonical rules NOT given (incidental good practice).

## Pre-declared outcomes
- P1 CEILING-LIFT: presented-strict at high density << low density (CIs separate).
- P2 FLAT: CIs overlap across densities (compliance is density-invariant).
