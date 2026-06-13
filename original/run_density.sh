#!/bin/bash
# run_v3_density.sh — AGET-Bench v3 Job B: TRUE instruction-density ladder (the H1 construct fix).
# Variants from build_density_variants.py: {d05,d10,d20,d30} = 1/2/4/6 rules per category (fixed mix),
# subsets of the canonical 30 (only scoreable range). ISOLATED run: each variant is copied into a fresh
# /tmp sandbox as AGENTS.md+CLAUDE.md so the repo-root config can't leak in ([[isolate_agent_empirical_tests]];
# the matrix-cN H1 cells did NOT isolate — possible ancestor-AGENTS.md confound, flagged 2026-06-13).
#
# RUN-CARD (standalone; per-invocation env -u CLAUDECODE):
#   bash poc/aget-bench/run_v3_density.sh                # dry-run
#   bash poc/aget-bench/run_v3_density.sh --execute      # opus x {d05,d10,d20,d30} x N=20 = 80 runs (cost-gated)
# API-billed (draws credits). Resume-safe: runs with non-empty response.txt are skipped.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
VS="$HERE/../vendor"
VARDIR="$HERE/variants/density"
N=20; EXECUTE=0; CAP=60; MODEL="claude-opus-4-8"
DENS="d05 d10 d20 d30"
RES="$HERE/results"
while [ $# -gt 0 ]; do case "$1" in --execute) EXECUTE=1; shift;; --n) N="$2"; shift 2;; --cap) CAP="$2"; shift 2;; --model) MODEL="$2"; shift 2;; *) shift;; esac; done
PROMPT="$(cat "$VS/task_prompt.txt")"

if [ "$EXECUTE" = 0 ]; then
  echo "[dry-run] Job B density ladder: $MODEL x {$DENS} x N=$N = $((4*N)) runs (isolated /tmp sandboxes)"
  for d in $DENS; do [ -s "$VARDIR/$d.md" ] && echo "  variant $d: $(wc -l < "$VARDIR/$d.md") lines" || echo "  MISSING $VARDIR/$d.md"; done
  echo "[dry-run] est ~\$$(python3 -c "print(f'{4*$N*0.32:.2f}')") @ ~\$0.32/run; cap \$$CAP"
  exit 0
fi
mkdir -p "$RES"
first=1
for d in $DENS; do
  src="$VARDIR/$d.md"
  [ -s "$src" ] || { echo "FATAL missing variant: $src"; exit 1; }
  cell="$RES/${d}__${MODEL//[.:]/_}"; mkdir -p "$cell"; ok=0; cost=0
  for i in $(seq 1 "$N"); do
    rd="$cell/run_$(printf '%02d' "$i")"; mkdir -p "$rd"
    if [ ! -s "$rd/response.txt" ]; then
      sbx="$(mktemp -d)"; cp "$src" "$sbx/AGENTS.md"; cp "$src" "$sbx/CLAUDE.md"
      ( cd "$sbx" && env -u CLAUDECODE claude -p "$PROMPT" --model "$MODEL" --output-format json </dev/null ) \
        > "$rd/raw.json" 2>/dev/null || true
      rm -rf "$sbx"
      c=$(python3 -c "import json;d=json.load(open('$rd/raw.json'));open('$rd/response.txt','w').write(d.get('result','') or '');print(d.get('total_cost_usd',0) or 0)" 2>/dev/null || echo 0)
      cost=$(python3 -c "print($cost + $c)")
    fi
    [ -s "$rd/response.txt" ] && ok=$((ok+1))
  done
  echo "$cost" >> "$RES/_spend.log"
  echo "  $d scoreable=$ok/$N cost=\$$(python3 -c "print(f'{$cost:.2f}')")"
  if [ -n "$first" ]; then
    first=""; proj=$(python3 -c "print(f'{$cost*4:.2f}')")
    echo "  [cost-gate B] cell-1 \$$(python3 -c "print(f'{$cost:.2f}')"), projected 4-cell \$$proj vs cap \$$CAP"
    over=$(python3 -c "print(1 if $cost*4 > $CAP else 0)"); [ "$over" = "1" ] && { echo "  ABORT: projection > cap."; exit 2; }
  fi
done
echo "=== Job B complete. Score: python3 score_density_ladder.py ==="
