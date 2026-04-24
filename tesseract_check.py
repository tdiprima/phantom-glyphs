#!/usr/bin/env python3
"""Run pytesseract on test_ocr.dcm and self-check against ground truth.

Usage:
    python tesseract_check.py [path/to/test_ocr.dcm]
"""

import sys

import numpy as np
import pydicom
import pytesseract
from PIL import Image

from check_ocr import find_substitutions, normalize, print_report
from create_test_dicom import REPORT_TEXT


def dicom_to_image(dicom_path):
    """Extract pixel data from DICOM and return a PIL Image."""
    ds = pydicom.dcmread(dicom_path)
    pixels = ds.pixel_array

    if pixels.dtype != np.uint8:
        pmin, pmax = float(pixels.min()), float(pixels.max())
        if pmax > pmin:
            pixels = ((pixels - pmin) / (pmax - pmin) * 255).astype(np.uint8)
        else:
            pixels = np.zeros_like(pixels, dtype=np.uint8)

    return Image.fromarray(pixels)


def run_tesseract(image):
    """Run pytesseract OCR on a PIL Image and return extracted text."""
    return pytesseract.image_to_string(image)


def main():
    dicom_path = sys.argv[1] if len(sys.argv) > 1 else "test_ocr.dcm"

    print(f"Reading DICOM: {dicom_path}")
    image = dicom_to_image(dicom_path)

    print("Running pytesseract OCR...\n")
    ocr_text = run_tesseract(image)

    print("=" * 60)
    print("PYTESSERACT OUTPUT")
    print("=" * 60)
    print(ocr_text)

    expected_lines = normalize(REPORT_TEXT)
    actual_lines = normalize(ocr_text)

    expected_flat = "\n".join(expected_lines)
    actual_flat = "\n".join(actual_lines)

    substitutions = find_substitutions(expected_lines, actual_lines)
    print_report(expected_flat, actual_flat, substitutions)


if __name__ == "__main__":
    main()
