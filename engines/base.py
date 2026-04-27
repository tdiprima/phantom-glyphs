#!/usr/bin/env python3
"""Base class for OCR engines."""

import abc

from PIL import Image


class OCREngine(abc.ABC):
    """Subclass this to add a new OCR engine.

    Steps:
      1. Create a module in engines/ with your subclass
      2. Implement name, is_available(), and run()
      3. Add your class to ENGINES in engines/__init__.py
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable engine name."""

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Return True if all dependencies are installed."""

    @abc.abstractmethod
    def run(self, image: Image.Image, work_dir: str) -> str:
        """Run OCR on a PIL Image. Use work_dir for temp files. Return extracted text."""
