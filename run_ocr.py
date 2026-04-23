#!/usr/bin/env python3
"""Read a DICOM image with Chandra OCR 2 and print extracted text.

Workflow:
  1. Extract pixel data from DICOM via pydicom
  2. Save as temporary PNG
  3. Run `chandra` CLI on the PNG
  4. Read generated markdown and print it
"""

import os
import subprocess
import sys
import tempfile

import numpy as np
import pydicom
from PIL import Image


def dicom_to_png(dicom_path, png_path):
    """Extract pixel data from a DICOM file and save as PNG."""
    ds = pydicom.dcmread(dicom_path)
    pixel_array = ds.pixel_array

    if pixel_array.dtype != np.uint8:
        pmin, pmax = float(pixel_array.min()), float(pixel_array.max())
        if pmax > pmin:
            pixel_array = ((pixel_array - pmin) / (pmax - pmin) * 255).astype(np.uint8)
        else:
            pixel_array = np.zeros_like(pixel_array, dtype=np.uint8)

    img = Image.fromarray(pixel_array)
    img.save(png_path)
    return png_path


def run_chandra(image_path, output_dir, method="hf"):
    """Run the chandra CLI on an image file."""
    cmd = ["chandra", image_path, output_dir, "--method", method]
    print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        print(f"STDERR:\n{result.stderr}", file=sys.stderr)
        raise RuntimeError(f"chandra exited with code {result.returncode}")


def find_markdown(output_dir):
    """Find the first .md file in the output directory tree."""
    for root, _dirs, files in os.walk(output_dir):
        for filename in files:
            if filename.endswith(".md"):
                return os.path.join(root, filename)
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_ocr.py <dicom_file> [--method hf|vllm]")
        sys.exit(1)

    dicom_path = sys.argv[1]
    method = "hf"
    if "--method" in sys.argv:
        method = sys.argv[sys.argv.index("--method") + 1]

    if not os.path.exists(dicom_path):
        print(f"Error: {dicom_path} not found", file=sys.stderr)
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        png_path = os.path.join(tmpdir, "dicom_image.png")
        print(f"Extracting pixels from {dicom_path}...")
        dicom_to_png(dicom_path, png_path)

        output_dir = os.path.join(tmpdir, "ocr_output")
        os.makedirs(output_dir)
        print(f"Running Chandra OCR ({method})...\n")
        run_chandra(png_path, output_dir, method)

        md_path = find_markdown(output_dir)
        if not md_path:
            print("No markdown output found. Files in output dir:")
            for root, _dirs, files in os.walk(output_dir):
                for f in files:
                    print(f"  {os.path.join(root, f)}")
            sys.exit(1)

        with open(md_path) as fh:
            text = fh.read()

        print("=" * 60)
        print("EXTRACTED TEXT")
        print("=" * 60)
        print(text)

        out_file = os.path.splitext(dicom_path)[0] + "_ocr_output.md"
        with open(out_file, "w") as fh:
            fh.write(text)
        print(f"\nSaved to: {out_file}")


if __name__ == "__main__":
    main()
