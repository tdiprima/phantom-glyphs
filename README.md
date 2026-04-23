# Phantom Glyphs

An OCR stress-test toolkit that generates DICOM medical images packed with visually confusing characters and measures how well OCR handles them.

## When `$500` Becomes `S500` on a Medical Bill

OCR engines routinely confuse characters that look nearly identical: `S` and `$`, `0` and `O`, `1` and `l` and `I`, `8` and `B`. In medical imaging, these errors aren't cosmetic. A misread dosage, a garbled patient ID, or a corrupted billing code can cascade into real clinical and financial problems. The challenge is that most OCR test sets use clean, well-separated text -- they don't stress the exact failure modes that matter in production.

## A Calibration Phantom for OCR

In medical imaging, a *phantom* is a standardized test object used to calibrate equipment. Phantom Glyphs applies the same idea to OCR: it generates a realistic radiology report embedded in a DICOM image, deliberately loaded with the character pairs that break OCR engines. Light scan noise simulates a real-world document. You run your OCR pipeline against it and see exactly where it fails.

The test report includes:

| Confusable Pair | Context in Report |
|----------------|-------------------|
| S vs $ | SOLOMON, SOB, S5 vs $500, $5,250, $1,250 |
| 0 vs O | O'BRIEN, OI01l0II01, 0.2cm, 0.51 |
| 1 vs l vs I | Il1O0oO01l, 1.1cm, Claire I., MRN field |
| 5 vs S | S5 segment, 5mm, 58-year-old, $5,250 |
| 8 vs B | B8B88b badge, rib #8, 6-8 weeks |
| Z vs 2 | Z-score vs -2.1 |

## What It Looks Like

Generate the test DICOM and run OCR in three commands:

```bash
# Create a DICOM image with the confusing-character report
python create_test_dicom.py

# Run Chandra OCR 2 on it
python run_ocr.py test_ocr.dcm
```

Output prints to the terminal and saves to `test_ocr_ocr_output.md`. A preview PNG is also generated so you can visually inspect the rendered text.

```
Confusing character pairs in this image:
  S vs $         | SOLOMON, SOB, S5 vs $500, $5,250, $1,250
  0 vs O         | O'BRIEN, SOLOMON, OI01l0II01, 0.2cm, 0.51
  1 vs l vs I    | Il1O0oO01l, 1.1cm, Claire I., MRN field
  5 vs S         | S5 segment, 5mm, 58-year-old, $5,250
  8 vs B         | B8B88b badge, rib #8, 6-8 weeks
  Z vs 2         | Z-score vs -2.1
```

## Getting Started

### Requirements

- Python 3.10+
- NVIDIA GPU with CUDA (for the HuggingFace method)
- ~10 GB disk for model weights on first run

### Install

```bash
uv add numpy pydicom pillow "chandra-ocr2[hf]"
```

Or use the provided install script:

```bash
bash install.sh
source venv/bin/activate
```

### Run

```bash
# Generate the test DICOM
python create_test_dicom.py

# Run OCR (default: HuggingFace backend)
python run_ocr.py test_ocr.dcm

# Or use a remote vLLM server instead of a local GPU
python run_ocr.py test_ocr.dcm --method vllm
```

### vLLM Server (No Local GPU)

If you don't have a local GPU, run the model on a remote server:

```bash
# On the GPU server
pip install chandra-ocr
chandra_vllm   # starts server on port 8000

# On your machine
export VLLM_API_BASE=http://your-gpu-server:8000/v1
python run_ocr.py test_ocr.dcm --method vllm
```

## Project Structure

| File | Purpose |
|------|---------|
| `create_test_dicom.py` | Renders a fake radiology report onto a DICOM image with scan noise |
| `run_ocr.py` | Extracts pixels from a DICOM, runs Chandra OCR 2, prints results |
| `install.sh` | Sets up a virtualenv with all dependencies |

## License

Chandra OCR 2 code is Apache 2.0. Model weights use a modified OpenRAIL-M license -- free for research, personal use, and startups under $2M revenue. Larger commercial use requires a [Datalab license](https://datalab.to).
