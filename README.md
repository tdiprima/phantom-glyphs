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

## Getting Started

### Requirements

- Python 3.10+
- NVIDIA GPU with CUDA (for Chandra OCR with HuggingFace backend)
- ~10 GB disk for model weights on first run
- Tesseract system binary (for the Tesseract comparison)

### Install

```bash
bash install.sh
source .venv/bin/activate
```

This installs Chandra OCR, pytesseract, and all dependencies into a `.venv` virtualenv.

For Tesseract, you also need the system binary:

```bash
# Ubuntu / Debian
sudo apt install tesseract-ocr

# RHEL / Rocky
sudo dnf install tesseract
```

### Run

The pipeline generates a test DICOM, runs both Chandra and Tesseract OCR on it, and compares their accuracy:

```bash
bash run-pipeline.sh
```

The five steps are:

1. **Generate** a DICOM image containing a fake radiology report with confusable characters
2. **Chandra OCR** reads the image
3. **Check Chandra** accuracy against ground truth
4. **Tesseract OCR** reads the same image (skipped if tesseract is not installed)
5. **Compare** both engines side-by-side and pick a winner

Output files are saved to the current directory:

| File | Contents |
|------|----------|
| `test_ocr.dcm` | Generated test DICOM |
| `test_ocr_preview.png` | Visual preview of the rendered text |
| `test_ocr_ocr_output.md` | Chandra OCR output |
| `test_ocr_tesseract_output.md` | Tesseract OCR output |

### Running Steps Individually

```bash
python create_test_dicom.py                 # generate test DICOM
python run_ocr.py test_ocr.dcm              # Chandra OCR (default: HuggingFace)
python check_ocr.py test_ocr_ocr_output.md  # check accuracy vs ground truth
python tesseract_check.py test_ocr.dcm      # Tesseract OCR + accuracy check
python compare_ocr.py                       # compare Chandra vs Tesseract
```

### vLLM Server (No Local GPU)

If you don't have a local GPU, run Chandra on a remote server:

```bash
# On the GPU server
pip install chandra-ocr
chandra_vllm   # starts server on port 8000

# On your machine
export VLLM_API_BASE=http://your-gpu-server:8000/v1
bash run-pipeline.sh --method vllm
```

## Project Structure

| File | Purpose |
|------|---------|
| `run-pipeline.sh` | Full pipeline: generate → Chandra → Tesseract → compare |
| `create_test_dicom.py` | Renders a fake radiology report onto a DICOM image with scan noise |
| `run_ocr.py` | Extracts pixels from a DICOM, runs Chandra OCR 2, saves results |
| `check_ocr.py` | Checks any OCR output against ground truth, reports accuracy and confusable-pair errors |
| `tesseract_check.py` | Runs Tesseract OCR on a DICOM and checks accuracy |
| `compare_ocr.py` | Side-by-side comparison of Chandra vs Tesseract with verdict |
| `install.sh` | Sets up a virtualenv with all dependencies |

## To add new engine — 3 steps: 
1. Create engines/yourengine.py, subclass OCREngine
2. Implement name, is_available(), run(image, work_dir)
3. Add to ENGINES list in engines/__init__.py


## License

Chandra OCR 2 code is Apache 2.0. Model weights use a modified OpenRAIL-M license -- free for research, personal use, and startups under $2M revenue. Larger commercial use requires a [Datalab license](https://datalab.to).
