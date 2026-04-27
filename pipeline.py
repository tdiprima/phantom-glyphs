#!/usr/bin/env python3
"""Run all available OCR engines on a DICOM, time each, compare metrics.

Usage:
    python pipeline.py [test_ocr.dcm] [--method hf|vllm]
"""

import os
import sys
import tempfile
import time

from check_ocr import compute_metrics
from create_test_dicom import REPORT_TEXT
from dicom_utils import dicom_to_image
from engines import ENGINES
from engines.chandra import ChandraEngine


def parse_args():
    """Parse CLI arguments. Return (dicom_path, method)."""
    dicom_path = "test_ocr.dcm"
    method = "hf"
    args = sys.argv[1:]
    positional = []
    idx = 0
    while idx < len(args):
        if args[idx] == "--method":
            if idx + 1 >= len(args):
                print("Error: --method requires a value (hf or vllm)", file=sys.stderr)
                sys.exit(1)
            method = args[idx + 1]
            idx += 2
        elif args[idx] in ("--help", "-h"):
            print(__doc__)
            sys.exit(0)
        else:
            positional.append(args[idx])
            idx += 1
    if positional:
        dicom_path = positional[0]
    return dicom_path, method


def build_engines(method):
    """Instantiate all registered engines, passing config where needed."""
    instances = []
    for engine_cls in ENGINES:
        if engine_cls is ChandraEngine:
            instances.append(engine_cls(method=method))
        else:
            instances.append(engine_cls())
    return instances


def run_engine(engine, image, work_dir):
    """Run one engine with timing. Return (text, elapsed) or (None, None)."""
    try:
        start = time.perf_counter()
        text = engine.run(image, work_dir)
        elapsed = time.perf_counter() - start
        return text, elapsed
    except Exception as exc:
        print(f"  ERROR: {exc}", file=sys.stderr)
        return None, None


def save_output(dicom_path, engine_name, text):
    """Save OCR text to a file named after the engine."""
    slug = engine_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
    out_file = os.path.splitext(dicom_path)[0] + f"_{slug}_output.md"
    with open(out_file, "w") as fh:
        fh.write(text)
    print(f"  Saved: {out_file}")
    return out_file


def print_engine_result(engine_name, metrics, elapsed):
    """Print per-engine metrics block."""
    print(f"\n{'=' * 60}")
    print(f"{engine_name}")
    print(f"{'=' * 60}")
    print(f"  Time:                 {elapsed:.2f}s")
    print(f"  Character accuracy:   {metrics['char_accuracy']:.2%}")
    print(f"  Word accuracy:        {metrics['word_accuracy']:.2%}")
    print(f"  Substitutions:        {metrics['total_substitutions']}")
    print(f"  Confusable errors:    {metrics['confusable_errors']}")


def print_comparison(results):
    """Print N-way comparison table across all engines that ran."""
    if len(results) < 2:
        return

    col_width = max(14, max(len(r["engine"]) for r in results) + 2)

    print(f"\n{'=' * (25 + (col_width + 1) * len(results))}")
    print("ENGINE COMPARISON")
    print(f"{'=' * (25 + (col_width + 1) * len(results))}")

    header = f"{'Metric':<25}"
    separator = "-" * 25
    for result in results:
        header += f" {result['engine']:>{col_width}}"
        separator += " " + "-" * col_width
    print(header)
    print(separator)

    rows = [
        ("Time (seconds)", "time_seconds", "{:.2f}"),
        ("Character accuracy", "char_accuracy", "{:.2%}"),
        ("Word accuracy", "word_accuracy", "{:.2%}"),
        ("Total substitutions", "total_substitutions", "{}"),
        ("Confusable-pair errors", "confusable_errors", "{}"),
    ]
    for label, key, fmt in rows:
        line = f"{label:<25}"
        for result in results:
            line += f" {fmt.format(result[key]):>{col_width}}"
        print(line)

    print()
    print_verdict(results)


def print_verdict(results):
    """Pick winner: confusable errors primary, char accuracy secondary, time tertiary."""
    ranked = sorted(results, key=lambda r: (
        r["confusable_errors"],
        -r["char_accuracy"],
        r["time_seconds"],
    ))

    best = ranked[0]
    second = ranked[1]
    is_tie = (
        best["confusable_errors"] == second["confusable_errors"]
        and best["char_accuracy"] == second["char_accuracy"]
    )

    if is_tie:
        print("VERDICT: Tie — identical accuracy metrics.")
        return

    reasons = []
    if best["confusable_errors"] <= min(r["confusable_errors"] for r in results):
        reasons.append("fewest confusable errors")
    if best["char_accuracy"] >= max(r["char_accuracy"] for r in results):
        reasons.append("highest character accuracy")
    if best["time_seconds"] <= min(r["time_seconds"] for r in results):
        reasons.append("fastest")

    print(f"VERDICT: {best['engine']} — {', '.join(reasons)}.")


def main():
    dicom_path, method = parse_args()

    if not os.path.exists(dicom_path):
        print(f"Error: {dicom_path} not found", file=sys.stderr)
        sys.exit(1)

    print(f"Loading DICOM: {dicom_path}")
    image = dicom_to_image(dicom_path)

    engines = build_engines(method)
    available = [e for e in engines if e.is_available()]
    skipped = [e for e in engines if not e.is_available()]

    for engine in skipped:
        print(f"[SKIP] {engine.name}: dependencies not available")

    if not available:
        print("No OCR engines available. Install at least one.", file=sys.stderr)
        sys.exit(1)

    print(f"\nEngines available: {', '.join(e.name for e in available)}")

    results = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for engine in available:
            print(f"\nRunning {engine.name}...")
            engine_dir = os.path.join(tmpdir, engine.name.replace(" ", "_"))
            os.makedirs(engine_dir, exist_ok=True)

            text, elapsed = run_engine(engine, image, engine_dir)
            if text is None:
                continue

            save_output(dicom_path, engine.name, text)
            metrics = compute_metrics(REPORT_TEXT, text)
            metrics["engine"] = engine.name
            metrics["time_seconds"] = elapsed
            results.append(metrics)

            print_engine_result(engine.name, metrics, elapsed)

    print_comparison(results)


if __name__ == "__main__":
    main()
