import json
import time
import sys
from pathlib import Path
from typing import Optional

from core.ingestion import load_policies
from core.chunker import chunk_documents
from core.vectorstore import get_or_build_index
from crew import resolve_ticket
from models import ResolutionResult

TEST_TICKETS_PATH = Path("evaluation/test_tickets.json")
RESULTS_DIR       = Path("evaluation/results")
REPORT_PATH       = Path("evaluation/eval_report.md")


def load_test_cases() -> list[dict]:
    with open(TEST_TICKETS_PATH, "r") as f:
        return json.load(f)


def map_status_to_decision(result: ResolutionResult) -> str:
    """
    Map structured ResolutionResult fields to a decision label
    that matches the expected_decision values in test_tickets.json.
    Uses verdict and status fields — no keyword matching on raw text.
    """
    status  = (result.status  or "").lower()
    verdict = (result.verdict or "").lower()

    if status == "escalated" or "escalate" in verdict:
        return "escalate"

    if status in ("resolved", "needs_review"):
        decision_text = (result.decision or "").lower()
        result_text   = (result.result   or "").lower()

        # partial — restocking fee mentioned in decision
        if "restocking" in decision_text or "restocking" in result_text:
            return "partial"

        # deny — explicit denial keywords in decision
        deny_keywords = [
            "not eligible", "cannot be returned", "denied",
            "not covered", "ineligible", "no refund", "deny"
        ]
        if any(k in decision_text for k in deny_keywords):
            return "deny"

        # approve — default for resolved tickets
        return "approve"

    if status == "needs_info":
        return "needs_info"

    return "unknown"


def has_citations(result: ResolutionResult) -> bool:
    """Check if result contains citation markers."""
    text = (result.result or "") + (result.customer_response or "")
    return "source:" in text.lower() or "chunk_" in text.lower()


def run_single_case(case: dict, vectorstore) -> dict:
    case_id     = case["case_id"]
    ticket_text = case["ticket_text"]
    order       = case["order"]
    expected    = case["expected_decision"]

    print(f"\n{'='*60}")
    print(f"Running: {case_id} [{case['category']}]")
    print(f"Ticket : {ticket_text[:80]}...")
    print(f"Expected: {expected}")

    try:
        start  = time.time()
        result = resolve_ticket(ticket_text, order, vectorstore, verbose=False)
        elapsed = round(time.time() - start, 2)

        actual   = map_status_to_decision(result)
        citations = has_citations(result)
        passed   = actual == expected

        print(f"Actual  : {actual} | Status: {result.status} | Verdict: {result.verdict}")
        print(f"Citations: {citations} | Passed: {passed} | Time: {elapsed}s")

        # save raw result
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        out = {
            "case_id":   case_id,
            "status":    result.status,
            "verdict":   result.verdict,
            "decision":  result.decision,
            "result":    result.result,
            "customer_response": result.customer_response,
        }
        (RESULTS_DIR / f"{case_id}.json").write_text(
            json.dumps(out, indent=2), encoding="utf-8"
        )

        return {
            "case_id":            case_id,
            "category":           case["category"],
            "expected_decision":  expected,
            "actual_decision":    actual,
            "status":             result.status,
            "verdict":            result.verdict,
            "has_citations":      citations,
            "passed":             passed,
            "elapsed_seconds":    elapsed,
            "notes":              case.get("notes", ""),
        }

    except Exception as e:
        print(f"ERROR on {case_id}: {e}")
        return {
            "case_id":            case_id,
            "category":           case["category"],
            "expected_decision":  expected,
            "actual_decision":    None,
            "status":             "error",
            "verdict":            None,
            "has_citations":      False,
            "passed":             False,
            "elapsed_seconds":    0,
            "notes":              f"ERROR: {str(e)}",
        }


def generate_report(results: list[dict]) -> str:
    total   = len(results)
    passed  = sum(1 for r in results if r["passed"])
    cited   = sum(1 for r in results if r["has_citations"])
    errors  = sum(1 for r in results if r["status"] == "error")

    esc_cases    = [r for r in results if r["expected_decision"] == "escalate"]
    esc_correct  = sum(1 for r in esc_cases if r["actual_decision"] == "escalate")

    by_category: dict[str, list] = {}
    for r in results:
        by_category.setdefault(r["category"], []).append(r)

    report = f"""# Bazario Evaluation Report

## Summary

| Metric | Value |
|---|---|
| Total cases | {total} |
| Passed | {passed} / {total} ({round(passed/total*100)}%) |
| Citation coverage | {cited} / {total} ({round(cited/total*100)}%) |
| Correct escalation rate | {esc_correct} / {len(esc_cases)} |
| Errors | {errors} |

## Results by Category

"""
    for cat, cat_results in by_category.items():
        cat_passed = sum(1 for r in cat_results if r["passed"])
        report += f"### {cat.title()} ({cat_passed}/{len(cat_results)} passed)\n\n"
        report += "| Case ID | Expected | Actual | Status | Verdict | Citations | Pass |\n"
        report += "|---|---|---|---|---|---|---|\n"
        for r in cat_results:
            report += (
                f"| {r['case_id']} | {r['expected_decision']} | {r['actual_decision'] or '?'} "
                f"| {r['status']} | {r['verdict'] or '?'} "
                f"| {'yes' if r['has_citations'] else 'no'} "
                f"| {'✅' if r['passed'] else '❌'} |\n"
            )
        report += "\n"

    report += "## Failed Cases\n\n"
    failed = [r for r in results if not r["passed"]]
    if not failed:
        report += "All cases passed.\n"
    else:
        for r in failed:
            report += f"- **{r['case_id']}** [{r['category']}]: expected `{r['expected_decision']}`, got `{r['actual_decision']}` — {r['notes']}\n"

    return report


def run_eval(case_ids: Optional[list[str]] = None):
    print("Loading policy corpus and vector index...")
    docs   = load_policies()
    chunks = chunk_documents(docs)
    vs     = get_or_build_index(chunks)

    cases = load_test_cases()
    if case_ids:
        cases = [c for c in cases if c["case_id"] in case_ids]

    print(f"\nRunning {len(cases)} test cases...\n")
    results = []
    for case in cases:
        result = run_single_case(case, vs)
        results.append(result)
        time.sleep(2)  # small delay between cases

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results_path = RESULTS_DIR / "eval_results.json"
    results_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nResults saved to {results_path}")

    report = generate_report(results)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Report  saved to {REPORT_PATH}")
    print("\n" + report)

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Bazario evaluation suite.")
    parser.add_argument("--cases", nargs="+", help="Specific case IDs (e.g. TC-001 TC-009)")
    args = parser.parse_args()
    run_eval(case_ids=args.cases)