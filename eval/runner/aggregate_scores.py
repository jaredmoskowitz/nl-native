#!/usr/bin/env python3
"""Median-aggregate multiple blind judge reads and de-anonymize via the key.

Usage:
  aggregate_scores.py --key KEY.json --rubric RUBRIC.json read1.json [read2.json ...]

Each read JSON maps submission_<i> -> {criterion: score, ..., "composite": score}.
Output (stdout) maps the de-anonymized condition label -> median scores per
criterion and composite, across all reads.
"""
import argparse
import json
import statistics


def aggregate(reads, key, criteria):
    fields = list(criteria) + ["composite"]
    result = {}
    for sub_id, label in key.items():
        per_field = {}
        for field in fields:
            values = [r[sub_id][field] for r in reads if sub_id in r and field in r[sub_id]]
            per_field[field] = statistics.median(values) if values else None
        result[label] = per_field
    return result


def main():
    parser = argparse.ArgumentParser(description="Median-aggregate + de-anonymize judge reads.")
    parser.add_argument("--key", required=True, help="submission_<i> -> label key JSON")
    parser.add_argument("--rubric", required=True, help="quality rubric JSON (for criteria)")
    parser.add_argument("reads", nargs="+", help="judge read JSON files")
    args = parser.parse_args()

    with open(args.key) as fh:
        key = json.load(fh)
    with open(args.rubric) as fh:
        rubric = json.load(fh)
    reads = []
    for path in args.reads:
        with open(path) as fh:
            reads.append(json.load(fh))

    print(json.dumps(aggregate(reads, key, rubric["criteria"]), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
