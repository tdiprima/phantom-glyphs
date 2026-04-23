# Phantom Glyphs

<!--"phantom" = standard medical imaging test object.-->

Medical imaging people know what a phantom is (calibration test object), and it perfectly describes what this repo does — test OCR with characters that are phantoms of each other.

<!--uv add numpy pydicom pillow "chandra-ocr2[hf]"-->

---

Chandra OCR 2 — DICOM Text Extraction Test

Test [Chandra OCR 2](https://github.com/datalab-to/chandra) on DICOM medical images containing text with visually confusing characters (S/\$, 0/O, 1/l/I, 5/S, 8/B, Z/2).

## Requirements

- Python 3.10+
- NVIDIA GPU with CUDA (for HuggingFace method)
- ~10 GB disk for model weights on first run

No GPU? Use the [vLLM server method](#vllm-server-alternative) instead.

## Quick Start

```bash
# 1. Install
bash install.sh
source venv/bin/activate

# 2. Create test DICOM with confusing text
python create_test_dicom.py

# 3. Run OCR on the DICOM
python run_ocr.py test_ocr.dcm
```

That's it. Output prints to terminal and saves to `test_ocr_output.md`.

## What Each Script Does

### `install.sh`

Creates a virtualenv and installs:

- `chandra-ocr[hf]` — Chandra OCR 2 with HuggingFace/PyTorch backend
- `pydicom` — DICOM file handling
- `pillow`, `numpy` — image processing

### `create_test_dicom.py`

Generates a fake radiology report rendered onto a DICOM image. The report is designed with character pairs that are hard for OCR to distinguish:

| Pair | Where it appears |
|------|-----------------|
| S vs \$ | SOLOMON, SOB, S5 vs \$500, \$1,250 |
| 0 vs O | O'BRIEN, OI01l0II01, 0.2cm |
| 1 vs l vs I | Il1O0oO01l, 1.1cm, Claire I. |
| 5 vs S | S5, 5mm, \$5,250 |
| 8 vs B | B8B88b, rib #8, 6-8 weeks |
| Z vs 2 | Z-score, -2.1 |

Outputs:

- `test_ocr.dcm` — the DICOM file
- `test_ocr_preview.png` — visual preview

Custom output path: `python create_test_dicom.py my_image.dcm`

### `run_ocr.py`

Reads a DICOM file, extracts pixel data to a temp PNG, runs Chandra OCR, and prints the extracted text.

```bash
# Default (HuggingFace, local GPU)
python run_ocr.py test_ocr.dcm

# With vLLM server
python run_ocr.py test_ocr.dcm --method vllm
```

## vLLM Server Alternative

If you don't have a local GPU, run the model on a remote GPU server:

```bash
# On the GPU server
pip install chandra-ocr
chandra_vllm   # starts server on port 8000

# On your machine
pip install chandra-ocr   # base install, no torch needed
pip install pydicom pillow numpy

export VLLM_API_BASE=http://your-gpu-server:8000/v1
python run_ocr.py test_ocr.dcm --method vllm
```

## First Run

The first `run_ocr.py` execution downloads the Chandra OCR 2 model (~8 GB). Subsequent runs use the cached model. Download happens once per machine.

## License

Chandra OCR 2 code is Apache 2.0. Model weights use a modified OpenRAIL-M license — free for research, personal use, and startups under $2M revenue. Larger commercial use requires a [Datalab license](https://datalab.to).

<br>
