"""OCR engine registry.

To add a new engine:
  1. Create a module in engines/ with a class extending OCREngine
  2. Implement name, is_available(), and run()
  3. Import and append to ENGINES below
"""

from engines.chandra import ChandraEngine
from engines.lighton import LightOnEngine
from engines.tesseract import TesseractEngine

ENGINES = [
    ChandraEngine,
    TesseractEngine,
    LightOnEngine,
]
