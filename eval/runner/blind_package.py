#!/usr/bin/env python3
"""Produce a blind, randomized bundle of code submissions for the quality judge,
plus a private key mapping anonymized ids back to condition labels.

Usage:
  blind_package.py --out BUNDLE --key KEY.json --seed N label=dir [label=dir ...]

The BUNDLE contains submission_0/, submission_1/, ... each holding only the
*.swift files of one submission, with NO label in the directory name. The KEY
(written separately, never inside BUNDLE) maps submission_<i> -> label.
Deterministic given --seed.
"""
import argparse
import json
import os
import random
import shutil


def package(entries, out_dir, key_file, seed):
    order = list(range(len(entries)))
    random.Random(seed).shuffle(order)
    os.makedirs(out_dir, exist_ok=True)
    key = {}
    for sub_index, orig_index in enumerate(order):
        label, src = entries[orig_index]
        sub_name = "submission_%d" % sub_index
        dst = os.path.join(out_dir, sub_name)
        os.makedirs(dst, exist_ok=True)
        for name in sorted(os.listdir(src)):
            if name.endswith(".swift"):
                shutil.copy(os.path.join(src, name), os.path.join(dst, name))
        key[sub_name] = label
    with open(key_file, "w") as fh:
        json.dump(key, fh, indent=2, sort_keys=True)
    return key


def parse_entry(value):
    label, sep, path = value.partition("=")
    if not sep or not label or not path:
        raise argparse.ArgumentTypeError("expected label=dir, got %r" % value)
    return (label, path)


def main():
    parser = argparse.ArgumentParser(description="Blind-package submissions for the judge.")
    parser.add_argument("--out", required=True, help="output bundle directory")
    parser.add_argument("--key", required=True, help="path to write the private id->label key")
    parser.add_argument("--seed", type=int, required=True, help="deterministic shuffle seed")
    parser.add_argument("entries", nargs="+", type=parse_entry, help="label=dir pairs")
    args = parser.parse_args()
    package(args.entries, args.out, args.key, args.seed)


if __name__ == "__main__":
    main()
