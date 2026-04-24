#!/usr/bin/env python3
"""Compare OCR output against ground truth and report errors.

Computes character-level and word-level accuracy, then groups
misrecognitions by the confusable glyph pairs defined in the
test DICOM generator.

python check_ocr.py test_ocr_ocr_output.md
"""

import difflib
import re
import sys

from create_test_dicom import CONFUSING_PAIRS, REPORT_TEXT

CONFUSION_MAP = {
    "S vs $": set("S$"),
    "0 vs O": set("0O"),
    "1 vs l vs I": set("1lI"),
    "5 vs S": set("5S"),
    "8 vs B": set("8B"),
    "Z vs 2": set("Z2"),
}


def normalize(text):
    """Normalize whitespace for fair comparison."""
    lines = text.strip().splitlines()
    return [line.rstrip() for line in lines]


def character_accuracy(expected, actual):
    """Compute character-level accuracy via SequenceMatcher."""
    matcher = difflib.SequenceMatcher(None, expected, actual)
    return matcher.ratio()


def word_accuracy(expected, actual):
    """Compute word-level accuracy."""
    expected_words = expected.split()
    actual_words = actual.split()
    matcher = difflib.SequenceMatcher(None, expected_words, actual_words)
    return matcher.ratio()


def classify_error(expected_char, actual_char):
    """Return the confusion category for a character substitution, or None."""
    for label, chars in CONFUSION_MAP.items():
        if expected_char in chars and actual_char in chars:
            return label
    return None


def find_substitutions(expected_lines, actual_lines):
    """Walk aligned lines and find character-level substitutions."""
    line_matcher = difflib.SequenceMatcher(None, expected_lines, actual_lines)
    substitutions = []

    for tag, i1, i2, j1, j2 in line_matcher.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                exp_line = expected_lines[i1 + offset]
                act_line = actual_lines[j1 + offset]
                substitutions.extend(_char_subs(i1 + offset + 1, exp_line, act_line))
        elif tag == "replace":
            pairs = min(i2 - i1, j2 - j1)
            for offset in range(pairs):
                exp_line = expected_lines[i1 + offset]
                act_line = actual_lines[j1 + offset]
                substitutions.extend(_char_subs(i1 + offset + 1, exp_line, act_line))

    return substitutions


def _char_subs(line_num, exp_line, act_line):
    """Yield (line, col, expected, actual, category) for each substitution."""
    subs = []
    sm = difflib.SequenceMatcher(None, exp_line, act_line)
    for tag, ci1, ci2, cj1, cj2 in sm.get_opcodes():
        if tag == "replace":
            for k in range(min(ci2 - ci1, cj2 - cj1)):
                ec = exp_line[ci1 + k]
                ac = act_line[cj1 + k]
                category = classify_error(ec, ac)
                subs.append((line_num, ci1 + k + 1, ec, ac, category))
    return subs


def print_report(expected_text, actual_text, substitutions):
    """Print accuracy metrics and error details."""
    char_acc = character_accuracy(expected_text, actual_text)
    w_acc = word_accuracy(expected_text, actual_text)

    print("=" * 60)
    print("OCR SELF-CHECK REPORT")
    print("=" * 60)
    print(f"Character accuracy: {char_acc:.2%}")
    print(f"Word accuracy:      {w_acc:.2%}")
    print(f"Substitutions:      {len(substitutions)}")

    by_category = {}
    uncategorized = []
    for line, col, ec, ac, cat in substitutions:
        if cat:
            by_category.setdefault(cat, []).append((line, col, ec, ac))
        else:
            uncategorized.append((line, col, ec, ac))

    if by_category:
        print(f"\n--- Confusable-pair errors ({sum(len(v) for v in by_category.values())}) ---")
        for label, _ in CONFUSING_PAIRS:
            errors = by_category.get(label, [])
            if not errors:
                continue
            print(f"\n  [{label}] ({len(errors)} errors)")
            for line, col, ec, ac in errors:
                print(f"    L{line}:C{col}  expected '{ec}'  got '{ac}'")

    if uncategorized:
        print(f"\n--- Other substitutions ({len(uncategorized)}) ---")
        for line, col, ec, ac in uncategorized:
            print(f"    L{line}:C{col}  expected '{ec}'  got '{ac}'")

    if not substitutions:
        print("\nNo substitution errors detected.")

    print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_ocr.py <ocr_output.md>")
        sys.exit(1)

    ocr_path = sys.argv[1]
    with open(ocr_path) as fh:
        actual_raw = fh.read()

    expected_lines = normalize(REPORT_TEXT)
    actual_lines = normalize(actual_raw)

    expected_flat = "\n".join(expected_lines)
    actual_flat = "\n".join(actual_lines)

    substitutions = find_substitutions(expected_lines, actual_lines)
    print_report(expected_flat, actual_flat, substitutions)

    if substitutions:
        print("--- Line-by-line diff (first 40 diffs) ---")
        diff = difflib.unified_diff(
            expected_lines, actual_lines,
            fromfile="ground_truth", tofile="ocr_output",
            lineterm="",
        )
        count = 0
        for line in diff:
            print(line)
            if line.startswith(("+" , "-")) and not line.startswith(("+++", "---")):
                count += 1
                if count >= 40:
                    print("  ... (truncated)")
                    break
        print()


if __name__ == "__main__":
    main()
