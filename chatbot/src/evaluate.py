"""Score the chatbot against a fixed set of questions with known-good outcomes (eval/golden.json).

    python chatbot/src/evaluate.py                 # retrieval only: free, instant, no LLM
    python chatbot/src/evaluate.py --answers       # also asks the configured LLM and checks the wording

This is how a change to the prompt, the chunking or retrieval is judged: run it before and after. A change that
lowers the score does not ship. New failures found with report.py become new cases here, so they can't come back.

A case may have:
  question        (required)
  retrieved       chunk titles that must ALL appear among the retrieved chunks (substring match)
  retrieved_any   at least ONE of these titles must appear
  mention         (--answers) words the answer must contain (case-insensitive)
  not_mention     (--answers) text the answer must NOT contain
  unsupported     (--answers) true = the answer must cite nothing, because the CV does not contain the answer
  note            why the case exists
"""
import argparse
import json
import sys
from pathlib import Path

from retrieval import DEFAULT_K, retrieve

GOLDEN = Path(__file__).resolve().parents[1] / "eval" / "golden.json"


def load_cases(path=GOLDEN):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _present(title, titles):
    return any(title.lower() in candidate.lower() for candidate in titles)


def check_retrieval(case, k=DEFAULT_K, **options):
    """List of problems with what retrieval returned for this case (empty = pass)."""
    titles = [chunk["title"] for chunk in retrieve(case["question"], k=k, **options)]
    problems = [f"retrieval missed {want!r}" for want in case.get("retrieved", []) if not _present(want, titles)]
    wanted_any = case.get("retrieved_any")
    if wanted_any and not any(_present(want, titles) for want in wanted_any):
        problems.append(f"retrieval found none of {wanted_any}")
    return problems


def check_answer(case, answer):
    """List of problems with an `query.Answer` for this case (empty = pass)."""
    text = answer.answer.lower()
    problems = [f"answer does not mention {word!r}" for word in case.get("mention", []) if word.lower() not in text]
    problems += [f"answer contains {bad!r}" for bad in case.get("not_mention", []) if bad.lower() in text]
    if case.get("unsupported") and answer.sources:
        problems.append("answer cited sources for something the CV does not contain")
    return problems


def run(cases, answers=False, llm=None, **options):
    """[(case, problems)] for every case."""
    results = []
    for case in cases:
        problems = [] if case.get("unsupported") and not case.get("retrieved") else check_retrieval(case, **options)
        if answers:
            from query import answer

            problems += check_answer(case, answer(case["question"], llm=llm, **options))
        results.append((case, problems))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--answers", action="store_true", help="also call the LLM (costs a little, and is slower)")
    parser.add_argument("--file", default=str(GOLDEN))
    args = parser.parse_args()

    results = run(load_cases(args.file), answers=args.answers)
    for case, problems in results:
        print(f"{'FAIL' if problems else 'ok  '}  {case['question']}")
        for problem in problems:
            print(f"        - {problem}")
    passed = sum(not problems for _, problems in results)
    print(f"\n{passed}/{len(results)} passed" + ("" if args.answers else "  (retrieval only; add --answers to check the wording)"))
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
