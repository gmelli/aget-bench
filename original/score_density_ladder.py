#!/usr/bin/env python3
"""score_density_ladder.py — AGET-Bench v3 Job B: score the TRUE density ladder.

Answers H-ABV3-001 properly: does compliance with PRESENTED rules fall as instruction density rises?
For each density cell {d05,d10,d20,d30}, scores each response with the canonical score_rules, then splits:
  - PRESENTED compliance: strict pass-rate over the rules that density actually gave the subject (manifest.json)
  - UNPRESENTED compliance: pass-rate over canonical rules NOT given (baseline good-practice / incidental)
Wilson 95% CI on the pooled presented-rule pass proportion per density.

Usage: python3 score_density_ladder.py     (scores poc/aget-bench/results_v3_density)
"""
import os, sys, re, math, json, glob
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "vendor"))
from score_g2 import extract_code, score_rules  # noqa: E402

RES = os.path.join(HERE, "results")
MANIFEST = json.load(open(os.path.join(HERE, "variants", "density", "manifest.json")))
# manifest keys are density ints as strings ("5","10","20","30"); cells are d05/d10/d20/d30
DENS_OF = {"d05": "5", "d10": "10", "d20": "20", "d30": "30"}


def norm(rid):
    m = re.match(r'R-0*(\d+)', rid)
    return f"R-{int(m.group(1)):03d}" if m else rid


def wilson(p, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    ph = p / n
    d = 1 + z * z / n
    c = ph + z * z / (2 * n)
    m = z * math.sqrt((ph * (1 - ph) + z * z / (4 * n)) / n)
    return (max(0, (c - m) / d) * 100, min(1, (c + m) / d) * 100)


def main():
    if not os.path.isdir(RES):
        print(f"(no results yet: {RES})"); return
    print("# AGET-Bench v3 H1-proper — opus density ladder (compliance vs rule COUNT, isolated sandboxes)")
    print(f"# {'density':8} {'n':>3} {'PRESENTED strict% [Wilson95]':>30} {'UNPRESENTED strict%':>20}")
    rows = []
    for cell in sorted(os.listdir(RES)):
        cdir = os.path.join(RES, cell)
        if not os.path.isdir(cdir):
            continue
        dlabel = cell.split("__")[0]
        present = set(MANIFEST.get(DENS_OF.get(dlabel, ""), []))
        if not present:
            continue
        pp = pt = up = ut = n = degen = 0
        for f in sorted(glob.glob(os.path.join(cdir, "run_*", "response.txt"))):
            if os.path.getsize(f) == 0:
                continue
            code = extract_code(open(f).read())
            if not code.strip():
                degen += 1; continue
            n += 1
            res = score_rules(code)
            for rid, v in res.items():
                if v == "na":
                    continue
                nr = norm(rid)
                passed = 1 if v == "pass" else 0
                if nr in present:
                    pt += 1; pp += passed
                else:
                    ut += 1; up += passed
        lo, hi = wilson(pp, pt)
        rows.append((dlabel, len(present), n, pp, pt, lo, hi, up, ut, degen))
        upct = (100 * up / ut) if ut else 0
        print(f"  {dlabel} ({len(present):2d}r) {n:>3} "
              f"{pp}/{pt}={100*pp/pt if pt else 0:5.1f} [{lo:4.1f},{hi:4.1f}]      "
              f"{up}/{ut}={upct:5.1f}" + (f"  degen={degen}" if degen else ""))
    print("# PRESENTED = compliance with rules the subject was given (the H1 DV);")
    print("# UNPRESENTED = compliance with canonical rules NOT given (incidental good practice).")
    print("# H-ABV3-001: P1 CEILING-LIFT if presented-strict at high density << low density (CI-sep);")
    print("#             P2 FLAT if CIs overlap across densities (compliance is density-invariant).")


if __name__ == "__main__":
    main()
