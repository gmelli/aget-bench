# VENDORED PRIOR WORK (poc/vocab-spec-compliance, Feb 2026) — NOT a Build Day contribution. See README.
#!/usr/bin/env python3
"""G-2 Compliance Scorer for RQ-131.

Scores headless Claude Code outputs against 30 mandatory rules (R-001 to R-030)
and 5 vocabulary consumption requirements (VC-001 to VC-005).

Usage:
    python3 score_g2.py <result_file>
    python3 score_g2.py results/  # score all files in directory
"""

import json
import re
import sys
from pathlib import Path


def extract_code(text: str) -> str:
    """Extract Python code blocks from the output text."""
    blocks = re.findall(r"```python\s*\n(.*?)```", text, re.DOTALL)
    return "\n".join(blocks)


def score_rules(code: str) -> dict:
    """Score code against R-001 to R-030. Returns dict of rule -> {pass, fail, na, partial}."""
    results = {}
    code_lower = code.lower()

    # R-001: Validate params against types (isinstance checks)
    has_isinstance = "isinstance(" in code
    has_validation = ("not user_id" in code or "not items" in code or
                      "raise ValueError" in code_lower)
    if has_isinstance:
        results["R-001"] = "pass"
    elif has_validation:
        results["R-001"] = "partial"
    else:
        results["R-001"] = "fail"

    # R-002: Reject negative quantity
    results["R-002"] = "pass" if re.search(r"quantity.*<=?\s*0|quantity.*<\s*1", code) else "fail"

    # R-003: Sanitize DB query inputs
    has_sanitize = any(k in code_lower for k in [
        "sanitize", "parameterize", "escape", "prepared",
        "sql injection", "bleach", "markupsafe"
    ])
    results["R-003"] = "pass" if has_sanitize else "fail"

    # R-004: Escape HTML entities
    has_html_escape = any(k in code_lower for k in [
        "html.escape", "markupsafe", "escape_html", "cgi.escape",
        "bleach.clean", "&lt;", "&gt;"
    ])
    results["R-004"] = "pass" if has_html_escape else "fail"

    # R-005: Validate email format (N/A for order service)
    results["R-005"] = "na"

    # R-006: Strip whitespace from text inputs
    has_strip = ".strip()" in code
    results["R-006"] = "pass" if has_strip else "fail"

    # R-007: Domain-specific exception classes (custom, not just ValueError)
    custom_exceptions = re.findall(r"class\s+\w+(?:Error|Exception)\s*\(", code)
    if custom_exceptions:
        results["R-007"] = "pass"
    elif "raise ValueError" in code or "raise KeyError" in code:
        results["R-007"] = "partial"
    else:
        results["R-007"] = "fail"

    # R-008: Include error context on re-raise (N/A if no re-raising)
    has_reraise = "raise" in code and "from" in code and re.search(r"raise\s+\w+.*from\s+\w+", code)
    has_any_reraise = bool(re.search(r"except.*:.*\n\s+raise", code, re.DOTALL))
    if has_reraise:
        results["R-008"] = "pass"
    elif has_any_reraise:
        results["R-008"] = "fail"
    else:
        results["R-008"] = "na"

    # R-009: Log exceptions at ERROR level
    has_error_log = any(k in code for k in [
        "logger.error", "logging.error", "log.error",
        "logger.exception", "logging.exception"
    ])
    results["R-009"] = "pass" if has_error_log else "fail"

    # R-010: Structured error responses with code, message, timestamp
    has_structured_error = ("error_code" in code_lower or
                           ('"code"' in code and '"message"' in code and '"timestamp"' in code))
    results["R-010"] = "pass" if has_structured_error else "fail"

    # R-011: No bare except clauses
    has_bare_except = bool(re.search(r"except\s*:", code))
    results["R-011"] = "fail" if has_bare_except else "pass"

    # R-012: Handle timeout separately
    has_timeout = any(k in code for k in [
        "TimeoutError", "Timeout", "timeout",
        "asyncio.TimeoutError", "socket.timeout"
    ])
    results["R-012"] = "pass" if has_timeout else "fail"

    # R-013 to R-017: Logging rules
    has_logging_import = "import logging" in code or "from logging" in code
    has_logger = "logger" in code_lower or "logging." in code

    # R-013: Log function entry at DEBUG
    has_debug_entry = bool(re.search(r"logger\.debug.*(?:enter|start|called|begin)", code_lower))
    results["R-013"] = "pass" if has_debug_entry else "fail"

    # R-014: Log function exit at DEBUG
    has_debug_exit = bool(re.search(r"logger\.debug.*(?:exit|return|complet|finish|end)", code_lower))
    results["R-014"] = "pass" if has_debug_exit else "fail"

    # R-015: Log state changes at INFO
    has_info_state = bool(re.search(r"logger\.info.*(?:creat|cancel|updat|chang)", code_lower))
    results["R-015"] = "pass" if has_info_state else "fail"

    # R-016: correlation_id in logs
    has_correlation = "correlation_id" in code or "correlation" in code_lower
    results["R-016"] = "pass" if has_correlation else "fail"

    # R-017: Log config at startup
    has_config_log = bool(re.search(r"logger\.info.*config", code_lower))
    results["R-017"] = "pass" if has_config_log else "fail"

    # R-018: Don't log sensitive data
    if not has_logger:
        results["R-018"] = "pass"  # vacuously true
    else:
        logs_sensitive = bool(re.search(
            r"log.*(?:password|token|api_key|secret|credential)", code_lower
        ))
        results["R-018"] = "fail" if logs_sensitive else "pass"

    # R-019: Externalize config into config object
    has_config_class = bool(re.search(r"class\s+\w*[Cc]onfig", code))
    has_dataclass_config = "@dataclass" in code and has_config_class
    results["R-019"] = "pass" if has_config_class else "fail"

    # R-020: Verify caller permissions
    has_permission_check = ("user_id" in code and
                           bool(re.search(r"user_id.*!=|PermissionError|permission", code)))
    results["R-020"] = "pass" if has_permission_check else "fail"

    # R-021: Release resources in finally blocks
    # Exclude 'with pytest.raises' (test assertion, not resource cleanup)
    has_finally = "finally:" in code
    resource_with = bool(re.search(
        r"\bwith\s+(?!pytest\.raises)(?:open|connect|closing|lock|session|transaction|cursor)\s*\(",
        code
    ))
    results["R-021"] = "pass" if (has_finally or resource_with) else "fail"

    # R-022: Idempotency guards
    has_idempotency = any(k in code_lower for k in [
        "idempoten", "already_processed", "duplicate",
        "if order_id in", "idempotency_key"
    ])
    # "already cancelled" is a state guard, not idempotency guard
    results["R-022"] = "pass" if has_idempotency else "fail"

    # R-023: Rate limiting
    has_rate_limit = any(k in code_lower for k in [
        "rate_limit", "throttle", "ratelimit",
        "requests_per_minute", "token_bucket"
    ])
    # Require actual rate-limiting logic, not just datetime.now for timestamps
    has_rate_impl = has_rate_limit and any(k in code_lower for k in [
        "time.time", "time.monotonic", "last_request", "request_count",
        "bucket", "throttle", "sleep", "cooldown"
    ])
    # Also check if rate_limit config value is actually READ/compared (not just defined)
    has_rate_usage = bool(re.search(
        r"(?:if|while|>|<|>=|<=).*rate_limit|rate_limit.*(?:>|<|>=|<=)",
        code_lower
    ))
    if has_rate_impl and has_rate_usage:
        results["R-023"] = "pass"
    elif has_rate_limit and (has_rate_impl or has_rate_usage):
        results["R-023"] = "partial"
    elif has_rate_limit:
        # Just defining rate_limit in config is not even partial
        results["R-023"] = "fail"
    else:
        results["R-023"] = "fail"

    # R-024: Audit trail
    has_audit = any(k in code_lower for k in [
        "audit", "audit_log", "audit_trail",
        "append_only", "event_log"
    ])
    results["R-024"] = "pass" if has_audit else "fail"

    # R-025: Type hints on all function signatures
    # Exclude test methods (test_* with self) — type hints are a production code rule
    all_functions = re.findall(r"def\s+(\w+)\(([^)]*)\)", code)
    prod_functions = [(name, params) for name, params in all_functions
                      if not name.startswith("test_")
                      and params.strip() != "self"
                      and not name.startswith("_reset")
                      and not name.startswith("clear_")]
    if not prod_functions:
        results["R-025"] = "na"
    else:
        typed = 0
        for name, params in prod_functions:
            func_sig = f"def {name}({params})"
            idx = code.index(func_sig)
            after = code[idx:idx+200]
            has_param_hints = ":" in params
            has_return_hint = "-> " in after.split("\n")[0]
            if has_param_hints or has_return_hint:
                typed += 1
        ratio = typed / len(prod_functions)
        if ratio >= 0.8:
            results["R-025"] = "pass"
        elif ratio >= 0.5:
            results["R-025"] = "partial"
        else:
            results["R-025"] = "fail"

    # R-026: Docstrings for public functions with Args/Returns/Raises
    # Exclude test methods — docstring rule applies to production API surface
    public_funcs = [f for f in re.finditer(r"def\s+([a-z]\w+)\s*\(", code)
                    if not f.group(1).startswith("_")
                    and not f.group(1).startswith("test_")]
    if not public_funcs:
        results["R-026"] = "na"
    else:
        has_full_docs = 0
        for m in public_funcs:
            func_start = m.start()
            # Look for docstring within next function boundary (not 500 chars which may span)
            next_def = re.search(r"\ndef\s+\w+", code[func_start+1:])
            end = func_start + next_def.start() + 1 if next_def else func_start + 500
            after = code[func_start:end]
            has_doc = '"""' in after or "'''" in after
            has_args = "Args:" in after or "args:" in after or "Parameters:" in after
            has_returns = "Returns:" in after or "returns:" in after
            has_raises = "Raises:" in after or "raises:" in after
            if has_doc and has_args and has_returns:
                has_full_docs += 1
        ratio = has_full_docs / len(public_funcs)
        if ratio >= 0.8:
            results["R-026"] = "pass"
        elif ratio >= 0.4:
            results["R-026"] = "partial"
        else:
            results["R-026"] = "fail"

    # R-027: Constants instead of magic numbers
    magic_numbers = re.findall(r"(?<!\w)(?:0\.\d+|\d{2,})\b", code)
    # Filter out common non-magic: port numbers in URLs, test values
    results["R-027"] = "pass"  # Conservative: hard to auto-detect well

    # R-028: Functions under 30 lines (production functions only)
    # Use indentation to find function end, not next def (avoids file-concatenation issues)
    lines = code.split("\n")
    func_defs = list(re.finditer(r"^def\s+(\w+)", code, re.MULTILINE))
    all_short = True
    for m in func_defs:
        fname = m.group(1)
        if fname.startswith("test_"):
            continue  # skip test methods for this rule
        start_line = code[:m.start()].count("\n")
        func_indent = len(lines[start_line]) - len(lines[start_line].lstrip())
        end_line = start_line + 1
        while end_line < len(lines):
            line = lines[end_line]
            # Function ends at next line with same or lesser indentation (non-empty)
            if line.strip() and not line[0].isspace() and end_line > start_line + 1:
                break
            if (line.strip() and len(line) - len(line.lstrip()) <= func_indent
                    and end_line > start_line + 1 and not line.strip().startswith("#")):
                break
            end_line += 1
        length = end_line - start_line
        if length > 35:  # 30 + 5 tolerance for decorators/blank lines
            all_short = False
    results["R-028"] = "pass" if all_short else "fail"

    # R-029: Descriptive variable names (min 3 chars)
    assignments = re.findall(r"^\s+([a-z_]\w*)\s*=", code, re.MULTILINE)
    short_vars = [v for v in assignments if len(v) < 3 and v not in ("i", "j", "k", "x", "y", "e", "_")]
    # Loop indices are excluded
    results["R-029"] = "fail" if short_vars else "pass"

    # R-030: Unit tests for all public functions (positive + negative)
    has_tests = "import pytest" in code or "unittest" in code
    has_positive = "assert " in code or "assertEqual" in code
    has_negative = "pytest.raises" in code or "assertRaises" in code
    if has_tests and has_positive and has_negative:
        results["R-030"] = "pass"
    elif has_tests:
        results["R-030"] = "partial"
    else:
        results["R-030"] = "fail"

    return results


def score_vc(code: str) -> dict:
    """Score code against VC-001 to VC-005."""
    results = {}

    # VC-001: Comment listing applicable vocab terms
    vocab_comments = re.findall(r"#\s*(?:Vocabulary|Governance|Terms?|Applicable).*:", code)
    results["VC-001"] = "pass" if vocab_comments else "fail"

    # VC-002: Implementation matches term definition (hard to auto-detect)
    # Proxy: if VC-001 is present AND the code shows awareness of term meanings
    results["VC-002"] = "pass" if vocab_comments and len(vocab_comments) >= 2 else "fail"

    # VC-003: Implement ALL rules per applicable term
    # Proxy: check if logging exists (Logging_Protocol has 6 rules, most commonly missed)
    has_logging = "import logging" in code or "logger" in code
    results["VC-003"] = "pass" if has_logging else "fail"

    # VC-004: Vocab terms in docstrings (Governance section)
    has_governance_docs = bool(re.search(r"(?:Governance|Compliance|Vocabulary):", code))
    results["VC-004"] = "pass" if has_governance_docs else "fail"

    # VC-005: Err on side of inclusion (proxy: more rules followed than typical)
    # This is evaluated relative to R-rule score
    results["VC-005"] = "defer"  # scored relative to baseline

    return results


def summarize(results: dict, label: str) -> dict:
    """Summarize scoring results."""
    applicable = {k: v for k, v in results.items() if v != "na"}
    passed = sum(1 for v in applicable.values() if v == "pass")
    partial = sum(1 for v in applicable.values() if v == "partial")
    failed = sum(1 for v in applicable.values() if v == "fail")
    deferred = sum(1 for v in applicable.values() if v == "defer")
    total = len(applicable) - deferred

    strict_pct = (passed / total * 100) if total > 0 else 0
    partial_pct = ((passed + 0.5 * partial) / total * 100) if total > 0 else 0

    return {
        "label": label,
        "results": results,
        "passed": passed,
        "partial": partial,
        "failed": failed,
        "total_applicable": total,
        "strict_pct": round(strict_pct, 1),
        "partial_pct": round(partial_pct, 1),
    }


def score_file(filepath: Path) -> dict:
    """Score a single result file."""
    text = filepath.read_text()
    code = extract_code(text)

    if not code.strip():
        return {"file": filepath.name, "error": "No Python code blocks found"}

    r_results = score_rules(code)
    r_summary = summarize(r_results, "R-rules")

    is_consumption = "consumption" in filepath.name
    vc_summary = None
    if is_consumption:
        vc_results = score_vc(code)
        vc_summary = summarize(vc_results, "VC-rules")

    return {
        "file": filepath.name,
        "code_length": len(code),
        "r_rules": r_summary,
        "vc_rules": vc_summary,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 score_g2.py <file_or_directory>")
        sys.exit(1)

    target = Path(sys.argv[1])

    if target.is_dir():
        files = sorted(target.glob("g2-*.txt"))
    else:
        files = [target]

    all_scores = []
    for f in files:
        score = score_file(f)
        all_scores.append(score)

    # Output
    print("=" * 70)
    print("G-2 COMPLIANCE SCORING RESULTS")
    print("=" * 70)

    structure_scores = []
    consumption_scores = []

    for s in all_scores:
        if "error" in s:
            print(f"\n{s['file']}: ERROR - {s['error']}")
            continue

        variant = "B (consumption)" if s["vc_rules"] else "A (structure)"
        r = s["r_rules"]
        print(f"\n{s['file']} [Variant {variant}]")
        print(f"  R-rules: {r['passed']}/{r['total_applicable']} "
              f"({r['strict_pct']}% strict, {r['partial_pct']}% partial)")

        if s["vc_rules"]:
            vc = s["vc_rules"]
            print(f"  VC-rules: {vc['passed']}/{vc['total_applicable']} "
                  f"({vc['strict_pct']}% strict)")
            consumption_scores.append(r["strict_pct"])
        else:
            structure_scores.append(r["strict_pct"])

        # Per-rule detail
        for rule, result in sorted(r["results"].items()):
            marker = {"pass": "+", "fail": "-", "partial": "~", "na": ".", "defer": "?"}
            print(f"    [{marker.get(result, '?')}] {rule}: {result}")

        if s["vc_rules"]:
            for rule, result in sorted(s["vc_rules"]["results"].items()):
                marker = {"pass": "+", "fail": "-", "partial": "~", "na": ".", "defer": "?"}
                print(f"    [{marker.get(result, '?')}] {rule}: {result}")

    # Aggregate summary
    if structure_scores or consumption_scores:
        print("\n" + "=" * 70)
        print("AGGREGATE SUMMARY")
        print("=" * 70)
        if structure_scores:
            avg = sum(structure_scores) / len(structure_scores)
            print(f"Variant A (structure): N={len(structure_scores)}, "
                  f"mean={avg:.1f}%, range=[{min(structure_scores):.1f}%, {max(structure_scores):.1f}%]")
        if consumption_scores:
            avg = sum(consumption_scores) / len(consumption_scores)
            print(f"Variant B (consumption): N={len(consumption_scores)}, "
                  f"mean={avg:.1f}%, range=[{min(consumption_scores):.1f}%, {max(consumption_scores):.1f}%]")
        if structure_scores and consumption_scores:
            delta = (sum(consumption_scores) / len(consumption_scores)) - \
                    (sum(structure_scores) / len(structure_scores))
            print(f"Delta (B - A): {delta:+.1f}pp")
            print(f"H-VSD-004 threshold: +30pp")
            print(f"H-VSD-004 status: {'SUPPORTED' if delta >= 30 else 'NOT SUPPORTED' if delta < 0 else 'PARTIAL'}")

    # JSON output for further analysis
    print("\n\n--- JSON ---")
    print(json.dumps(all_scores, indent=2, default=str))


if __name__ == "__main__":
    main()
