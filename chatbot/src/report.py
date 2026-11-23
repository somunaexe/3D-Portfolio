"""Read the analytics log and show what needs a human's attention.

    python chatbot/src/report.py                 # last 7 days
    python chatbot/src/report.py --days 30
    python chatbot/src/report.py --export unsupported.jsonl     # questions to turn into evaluation cases

Point it at the live Redis with REDIS_URL (Railway: the Redis service's PUBLIC connection URL; never commit it).
Reading is the only thing it does.

How to use the report: the "unsupported" list is where the CV had no answer, retrieval missed it, or the question
was off topic. For each one decide which, fix the cause (add the fact to the CV, improve retrieval, adjust the
prompt) and add it to eval/golden.json so it can never silently regress.
"""
import argparse
import json
import re
import statistics
from collections import Counter

import redis

from analytics import QuestionLog
from memory import REDIS_URL


def normalise(text):
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(len(ordered) * fraction))]


def summarise(events, top=10):
    """A plain dict, so the report can be tested without printing."""
    ok = [e for e in events if e["status"] == "ok"]
    errors = [e for e in events if e["status"] == "error"]
    unsupported = Counter()
    wording = {}
    for event in ok:
        if not event["supported"]:
            key = normalise(event["standalone"])
            unsupported[key] += 1
            wording.setdefault(key, event["standalone"])
    cited_titles = Counter(title for e in ok for title in e["cited_titles"])
    latencies = [e["latency_ms"] for e in events]
    return {
        "total": len(events),
        "errors": len(errors),
        "unsupported_count": sum(unsupported.values()),
        "unsupported": [(wording[key], count) for key, count in unsupported.most_common(top)],
        "most_cited": cited_titles.most_common(top),
        "latency_ms_median": int(statistics.median(latencies)) if latencies else 0,
        "latency_ms_p95": percentile(latencies, 0.95) if latencies else 0,
    }


def print_report(summary, days):
    total = summary["total"]
    print(f"Last {days} days: {total} question(s), {summary['errors']} error(s)")
    if not total:
        print("Nothing logged. Is ANALYTICS_ENABLED=true on the service, and is REDIS_URL this report's Redis?")
        return
    share = 100 * summary["unsupported_count"] / max(1, total - summary["errors"])
    print(f"Answered without citing the CV: {summary['unsupported_count']} ({share:.0f}% of answered)")
    print(f"Time to answer: median {summary['latency_ms_median']} ms, slowest 5%: {summary['latency_ms_p95']} ms\n")
    print("Questions with no cited source (review these first):")
    for question, count in summary["unsupported"] or [("(none)", 0)]:
        print(f"  {count:>3} x  {question}")
    print("\nMost cited parts of the CV:")
    for title, count in summary["most_cited"] or [("(none)", 0)]:
        print(f"  {count:>3} x  {title}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--export", metavar="FILE", help="write the unsupported questions to FILE as JSON lines")
    args = parser.parse_args()

    client = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=5, socket_connect_timeout=5)
    try:
        events = QuestionLog(client).events(days=args.days)
    except redis.RedisError as error:
        raise SystemExit(f"Could not read Redis ({error}). Check REDIS_URL.")
    print_report(summarise(events), args.days)
    if args.export:
        rows = [{"question": e["standalone"], "retrieved": e["retrieved"], "cited": e["cited"]}
                for e in events if e["status"] == "ok" and not e["supported"]]
        with open(args.export, "w", encoding="utf-8") as handle:
            handle.writelines(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
        print(f"\nWrote {len(rows)} question(s) to {args.export}")


if __name__ == "__main__":
    main()
