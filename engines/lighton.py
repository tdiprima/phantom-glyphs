#!/usr/bin/env python3
"""LightOn OCR engine — template for integration.

To complete this engine:
  1. Install the LightOn OCR package (pip install lightonocr or equivalent)
  2. Update is_available() with the correct import
  3. Fill in run() with the actual API call
"""

from engines.base import OCREngine


class LightOnEngine(OCREngine):

    @property
    def name(self):
        return "LightOn"

    def is_available(self):
        try:
            import lightonocr  # noqa: F401
            return True
        except ImportError:
            return False

    def run(self, image, work_dir):
        import lightonocr
        raise NotImplementedError(
            "Fill in LightOn OCR API call — see engines/lighton.py"
        )
