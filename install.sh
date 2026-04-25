#!/usr/bin/env bash
set -euo pipefail

echo "=== Chandra OCR 2 - Install ==="

if [[ ! -d ".venv" ]]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing chandra-ocr with HuggingFace backend..."
pip install "chandra-ocr[hf]"

echo "Installing DICOM and image dependencies..."
pip install pydicom pillow numpy

echo "Installing pytesseract..."
pip install pytesseract

echo ""
echo "=== Install complete ==="
echo ""
echo "Activate environment before running scripts:"
echo "  source .venv/bin/activate"
echo ""
echo "NOTE: Tesseract requires the system binary:"
echo "  Ubuntu/Debian: sudo apt install tesseract-ocr"
echo "  RHEL/Rocky:    sudo dnf install tesseract"
echo ""
echo "NOTE: HuggingFace method requires a CUDA GPU."
echo "For CPU-only machines, use the vLLM server method instead:"
echo "  pip install chandra-ocr     # lighter install, no torch"
echo "  chandra_vllm                # start server (needs GPU host)"
echo "  chandra input.png ./output --method vllm"
