#!/usr/bin/env python3
"""build_density_variants.py — AGET-Bench v3 Job B: author a TRUE instruction-density ladder.

Construct fix (2026-06-13): the existing matrix-c1..c4 are a vocab x rules factorial, NOT a
density ladder, so H-ABV3-001 ("does compliance fall as rule COUNT rises?") was unresolvable.
This builds proper density variants by SUBSETTING the canonical 30 rules (the only rules
score_g2.py can score) at a FIXED category mix: k rules per each of 5 categories.

Densities: {5,10,20,30} = k in {1,2,4,6} per category (Input/Error/Logging/Architecture/Quality).
(Cannot exceed 30 — only 30 canonical rules exist; the prereg's "d60" was never scoreable.)

Emits, under poc/aget-bench/variants/density/:
  d05.md d10.md d20.md d30.md   — AGENTS.md content (header + the presented rule subset)
  manifest.json                 — {density: [presented R-IDs]} for the density-aware scorer

Usage: python3 build_density_variants.py
"""
import os, re, json
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "vendor", "corpus_30_rules.md")
OUT = os.path.join(HERE, "variants", "density")

# 5 categories, 6 rules each, in canonical order
CATS = [("Input & Data", range(1, 7)), ("Error Handling", range(7, 13)),
        ("Logging", range(13, 19)), ("Architecture", range(19, 25)),
        ("Quality", range(25, 31))]
PER_CAT = {5: 1, 10: 2, 20: 4, 30: 6}


def load_rules():
    text = open(SRC).read()
    rules = {}
    for m in re.finditer(r'^(R-0*(\d{1,3})):\s*(.+)$', text, re.M):
        rules[int(m.group(2))] = m.group(0).strip()
    assert len(rules) == 30, f"expected 30 canonical rules, got {len(rules)}"
    return rules


def main():
    os.makedirs(OUT, exist_ok=True)
    rules = load_rules()
    manifest = {}
    for dens, k in PER_CAT.items():
        present = []
        for _, idxs in CATS:
            present += list(idxs)[:k]
        present = sorted(present)
        manifest[dens] = [f"R-{i:03d}" for i in present]
        lines = ["# Agent Configuration", "", "## Mandatory Rules", "",
                 f"The agent SHALL follow all {len(present)} rules below when implementing code.", ""]
        for cat, idxs in CATS:
            sel = [i for i in idxs if i in present]
            if not sel:
                continue
            lines.append(f"### {cat} Rules")
            lines.append("")
            for i in sel:
                lines.append(rules[i])
            lines.append("")
        open(os.path.join(OUT, f"d{dens:02d}.md"), "w").write("\n".join(lines).rstrip() + "\n")
        print(f"  d{dens:02d}: {len(present)} rules ({k}/category) -> {os.path.relpath(os.path.join(OUT, f'd{dens:02d}.md'), HERE)}")
    json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=2)
    print(f"  manifest.json: " + " | ".join(f"d{d}={len(v)}" for d, v in manifest.items()))


if __name__ == "__main__":
    main()
