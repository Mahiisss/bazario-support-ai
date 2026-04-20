import json
import time
from pathlib import Path
from typing import Optional

from core.ingestion import load_policies
from core.chunker import chunk_documents
from core.vectorstore import get_or_build_index
from crew import resolve_ticket


TEST_TICKETS_PATH = Path("evaluation/test_tickets.json")
RESULTS_DIR = Path("evaluation/results")
REPORT_PATH = Path("evaluation/eval_report.md")


def load_test_cases() -> list[dict]:
    with open(TEST_TICKETS_PATH, "r") as f:
        return json.load(f)


def extract_decision(output: str) -> Optional[str]:
    """
    Tries to pull the decision out of the raw output string.
    Looks for keywords in the Decision or Compliance Verdict sections.
    Not perfect but good enough for eval purposes.
    """
    output_lower = output.lower()

    if "escalate to human agent" in output_lower or "escalate" in output_lower:
        return "escalate"
    if "partial refund" in output_lower or "partial" in output_lower:
        return "partial"
    if "approved" in output_lower or "full refund" in output_lower:
        return "approve"
    if "denied" in output_lower or "not eligible" in output_lower or "cannot" in output_lower:
        return "deny"

    return None


def has_citations(output: str) -> bool:
    """Check if the output contains citation markers."""
    return "source:" in output.lower() or "chunk_" in output.lower()


def check_correct_escalation(expected: str, actual: Optional[str]) -> Optional[bool]:
    """Only relevant for conflict and not_in_policy cases."""
    if expected == "escalate":
        return actual == "escalate"
    return None


def run_single_case(case: dict, vectorstore) -> dict:
    ticket_text = case["ticket_text"]
    order = case["order"]
    case_id = case["case_id"]

    print(f"\n{'='*60}")
    print(f"Running: {case_id} [{case['category']}]")
    print(f"Ticket: {ticket_text[:100]}...")
    print(f"Expected: {case['expected_decision']}")

    try:
        start = time.time()
        raw_output = resolve_ticket(ticket_text, order, vectorstore, verbose=False)
        elapsed = round(time.time() - start, 2)

        actual_decision = extract_decision(raw_output)
        citations = has_citations(raw_output)
        correct_esc = check_correct_escalation(case["expected_decision"], actual_decision)
        passed = actual_decision == case["expected_decision"]

        print(f"Actual  : {actual_decision} | Citations: {citations} | Passed: {passed} | Time: {elapsed}s")

        # save raw output
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        (RESULTS_DIR / f"{case_id}.txt").write_text(raw_output, encoding="utf-8")

        return {
            "case_id": case_id,
            "category": case["category"],
            "expected_decision": case["expected_decision"],
            "actual_decision": actual_decision,
            "has_citations": citations,
            "correct_escalation": correct_esc,
            "passed": passed,
            "elapsed_seconds": elapsed,
            "notes": case.get("notes", ""),
        }

    except Exception as e:
        print(f"ERROR on {case_id}: {e}")
        return {
            "case_id": case_id,
            "category": case["category"],
            "expected_decision": case["expected_decision"],
            "actual_decision": None,
            "has_citations": False,
            "correct_escalation": None,
            "passed": False,
            "elapsed_seconds": 0,
            "notes": f"ERROR: {str(e)}",
        }


def generate_report(results: list[dict]) -> str:
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    with_citations = sum(1 for r in results if r["has_citations"])

    escalation_cases = [r for r in results if r["expected_decision"] == "escalate"]
    correct_escalations = sum(1 for r in escalation_cases if r["correct_escalation"])

    # unsupported claim rate — cases that passed but had no citations
    passed_no_citations = sum(1 for r in results if r["passed"] and not r["has_citations"])

    report = f"""# Bazario Agent Evaluation Report

## Summary

| Metric | Value |
|---|---|
| Total cases | {total} |
| Passed | {passed} / {total} ({round(passed/total*100)}%) |
| Citation coverage | {with_citations} / {total} ({round(with_citations/total*100)}%) |
| Correct escalation rate | {correct_escalations} / {len(escalation_cases)} ({round(correct_escalations/max(len(escalation_cases),1)*100)}%) |
| Passed but no citations | {passed_no_citations} |

## Results by Case

| Case ID | Category | Expected | Actual | Citations | Passed |
|---|---|---|---|---|---|
"""

    for r in results:
        citations_str = "yes" if r["has_citations"] else "no"
        passed_str = "pass" if r["passed"] else "FAIL"
        report += (
            f"| {r['case_id']} | {r['category']} | {r['expected_decision']} "
            f"| {r['actual_decision'] or 'none'} | {citations_str} | {passed_str} |\n"
        )

    report += "\n## Notes\n"
    for r in results:
        if not r["passed"] or r["notes"].startswith("ERROR"):
            report += f"- **{r['case_id']}**: {r['notes']}\n"

    return report


def run_eval(case_ids: Optional[list[str]] = None):
    """
    Runs the full eval suite. Pass case_ids to run a subset.
    e.g. run_eval(["TC-001", "TC-009"]) for spot checks.
    """
    print("Loading policy corpus and vector index...")
    docs = load_policies()
    chunks = chunk_documents(docs)
    vs = get_or_build_index(chunks)

    cases = load_test_cases()
    if case_ids:
        cases = [c for c in cases if c["case_id"] in case_ids]

    print(f"\nRunning {len(cases)} test cases...\n")
    results = []
    for case in cases:
        result = run_single_case(case, vs)
        results.append(result)
        time.sleep(1)  # small delay to avoid hitting rate limits

    # save results JSON
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results_path = RESULTS_DIR / "eval_results.json"
    results_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nResults saved to {results_path}")

    # generate and save markdown report
    report = generate_report(results)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Report saved to {REPORT_PATH}")
    print("\n" + report)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run evaluation suite.")
    parser.add_argument(
        "--cases", nargs="+", help="Specific case IDs to run (e.g. TC-001 TC-009)"
    )
    args = parser.parse_args()

    run_eval(case_ids=args.cases)
