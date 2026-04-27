#!/usr/bin/env python3
"""Tesseract OCR engine via pytesseract."""

import shutil

from engines.base import OCREngine


class TesseractEngine(OCREngine):

    @property
    def name(self):
        return "Tesseract"

    def is_available(self):
        if shutil.which("tesseract") is None:
            return False
        try:
            import pytesseract  # noqa: F401
            return True
        except ImportError:
            return False

    def run(self, image, work_dir):
        import pytesseract
        return pytesseract.image_to_string(image)
