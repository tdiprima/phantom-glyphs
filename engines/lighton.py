#!/usr/bin/env python3
"""LightOn OCR engine via vLLM's OpenAI-compatible API.

LightOnOCR is a 1B-parameter model served through vLLM.
Requires a running vLLM server with the model loaded.

Configuration (environment variables):
  LIGHTON_BASE_URL  vLLM server URL (default: http://localhost:8000/v1)
  LIGHTON_MODEL     Model name as served (default: lightonai/LightOnOCR)
"""

import base64
import os

from engines.base import OCREngine

DEFAULT_BASE_URL = "http://localhost:8000/v1"
DEFAULT_MODEL = "lightonai/LightOnOCR"


class LightOnEngine(OCREngine):

    def __init__(self):
        self.base_url = os.environ.get("LIGHTON_BASE_URL", DEFAULT_BASE_URL)
        self.model = os.environ.get("LIGHTON_MODEL", DEFAULT_MODEL)

    @property
    def name(self):
        return "LightOn"

    def is_available(self):
        """Check openai package installed and vLLM server has model loaded."""
        try:
            from openai import OpenAI
        except ImportError:
            return False
        try:
            client = OpenAI(
                base_url=self.base_url,
                api_key="not-needed",
                timeout=5.0,
            )
            models = client.models.list()
            return any(self.model in m.id for m in models.data)
        except Exception:
            return False

    def run(self, image, work_dir):
        """Send image to vLLM server, return extracted text."""
        from openai import OpenAI

        png_path = os.path.join(work_dir, "input.png")
        image.save(png_path)

        with open(png_path, "rb") as fh:
            image_b64 = base64.b64encode(fh.read()).decode()

        client = OpenAI(base_url=self.base_url, api_key="not-needed")
        response = client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                    {"type": "text", "text": "Extract all text from this image."},
                ],
            }],
            max_tokens=4096,
        )
        return response.choices[0].message.content
