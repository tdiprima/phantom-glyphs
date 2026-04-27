#!/usr/bin/env python3
"""Chandra OCR 2 engine."""

import os
import re
import shutil
import subprocess
import sys

from engines.base import OCREngine


class ChandraEngine(OCREngine):

    def __init__(self, method="hf"):
        self.method = method

    @property
    def name(self):
        return f"Chandra ({self.method})"

    def is_available(self):
        return shutil.which("chandra") is not None

    def run(self, image, work_dir):
        png_path = os.path.join(work_dir, "input.png")
        image.save(png_path)

        output_dir = os.path.join(work_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        cmd = ["chandra", png_path, output_dir, "--method", self.method]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"STDERR:\n{result.stderr}", file=sys.stderr)
            raise RuntimeError(f"chandra exited with code {result.returncode}")

        md_path = self._find_markdown(output_dir)
        if not md_path:
            raise RuntimeError("chandra produced no markdown output")

        with open(md_path) as fh:
            text = fh.read()
        return self._clean_duplicate_markers(text)

    @staticmethod
    def _find_markdown(directory):
        for root, _dirs, files in os.walk(directory):
            for filename in files:
                if filename.endswith(".md"):
                    return os.path.join(root, filename)
        return None

    @staticmethod
    def _clean_duplicate_markers(text):
        text = re.sub(r"^(\d+\.)\s+\1", r"\1", text, flags=re.MULTILINE)
        text = re.sub(r"^(-)\s+\1", r"-", text, flags=re.MULTILINE)
        return text
