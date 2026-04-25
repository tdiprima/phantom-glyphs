#!/usr/bin/env python3
"""Compare Chandra and Tesseract OCR accuracy on the same test image.

Usage:
    python compare_ocr.py [chandra_output.md] [tesseract_output.md]
"""

import sys

from check_ocr import compute_metrics
from create_test_dicom import REPORT_TEXT


def print_comparison(chandra, tesseract):
    """Print side-by-side metrics and verdict."""
    print("=" * 60)
    print("OCR ENGINE COMPARISON")
    print("=" * 60)
    print(f"{'Metric':<25} {'Chandra':>12} {'Tesseract':>12}")
    print("-" * 50)
    print(f"{'Character accuracy':<25} {chandra['char_accuracy']:>11.2%} {tesseract['char_accuracy']:>11.2%}")
    print(f"{'Word accuracy':<25} {chandra['word_accuracy']:>11.2%} {tesseract['word_accuracy']:>11.2%}")
    print(f"{'Total substitutions':<25} {chandra['total_substitutions']:>12} {tesseract['total_substitutions']:>12}")
    print(f"{'Confusable-pair errors':<25} {chandra['confusable_errors']:>12} {tesseract['confusable_errors']:>12}")


def judge(chandra, tesseract):
    """Pick winner. Confusable-pair errors primary, char accuracy tiebreaker."""
    if chandra["confusable_errors"] < tesseract["confusable_errors"]:
        return "Chandra", "fewer confusable-pair errors"
    if tesseract["confusable_errors"] < chandra["confusable_errors"]:
        return "Tesseract", "fewer confusable-pair errors"
    if chandra["char_accuracy"] > tesseract["char_accuracy"]:
        return "Chandra", "higher character accuracy (confusable errors tied)"
    if tesseract["char_accuracy"] > chandra["char_accuracy"]:
        return "Tesseract", "higher character accuracy (confusable errors tied)"
    return None, "identical metrics"


def main():
    chandra_path = sys.argv[1] if len(sys.argv) > 1 else "test_ocr_ocr_output.md"
    tesseract_path = sys.argv[2] if len(sys.argv) > 2 else "test_ocr_tesseract_output.md"

    with open(chandra_path) as fh:
        chandra_text = fh.read()
    with open(tesseract_path) as fh:
        tesseract_text = fh.read()

    chandra = compute_metrics(REPORT_TEXT, chandra_text)
    tesseract = compute_metrics(REPORT_TEXT, tesseract_text)

    print_comparison(chandra, tesseract)

    winner, reason = judge(chandra, tesseract)
    print()
    if winner:
        print(f"VERDICT: {winner} — {reason}.")
    else:
        print(f"VERDICT: Tie — {reason}.")
    print()


if __name__ == "__main__":
    main()
