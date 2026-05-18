# Phantom Glyphs 👻 🌫️ 🫥 🌑 🕯️

An OCR stress-test toolkit that generates DICOM medical images packed with visually confusing characters and measures how well OCR handles them.

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
- NVIDIA GPU with CUDA (for GPU-based engines)
- Tesseract system binary (optional, for Tesseract engine)

### Install

```bash
bash install.sh
source .venv/bin/activate
```

For Tesseract, you also need the system binary:

```bash
# Ubuntu / Debian
sudo apt install tesseract-ocr

# RHEL / Rocky
sudo dnf install tesseract
```

### Run

The pipeline generates a test DICOM, runs all available OCR engines, times each one, and compares their accuracy:

```bash
bash run-pipeline.sh
```

Or run the pipeline directly:

```bash
python create_test_dicom.py          # generate test DICOM
python pipeline.py test_ocr.dcm     # run all available engines, compare
```

The pipeline automatically discovers which engines are available, skips the rest, and prints a comparison table with timing when two or more engines run.

To check a single output file against ground truth:

```bash
python check_ocr.py test_ocr_tesseract_output.md
```

## OCR Engines

The pipeline uses a plugin architecture. Each engine lives in `engines/` and is auto-discovered at runtime. Unavailable engines are skipped.

### Tesseract

Requires the `tesseract` system binary and `pytesseract` Python package (installed by `install.sh`).

### Chandra OCR 2

Runs via the `chandra` CLI. Install with:

```bash
pip install "chandra-ocr[hf]"
```

For the vLLM backend instead of HuggingFace:

```bash
# On a GPU server
pip install chandra-ocr
chandra_vllm   # starts server on port 8000

# Run pipeline with vLLM backend
bash run-pipeline.sh --method vllm
```

### LightOn OCR

LightOnOCR is a 1B-parameter model served through [vLLM](https://docs.vllm.ai/). It uses the standard OpenAI-compatible API, so the pipeline talks to it via the `openai` Python package.

**1. Install the `openai` package:**

```bash
pip install openai
```

**2. Start a vLLM server with the LightOnOCR model:**

```bash
# Docker (recommended) — needs vLLM >= 0.18.0 and transformers >= 5.4.0
docker run --gpus all -p 8000:8000 \
    vllm/vllm-openai:latest \
    --model lightonai/LightOnOCR \
    --max-model-len 4096

# Or system install
pip install vllm
vllm serve lightonai/LightOnOCR --max-model-len 4096
```

If vLLM doesn't recognize the model class, build a custom image that upgrades `transformers`:

```dockerfile
FROM vllm/vllm-openai:latest
RUN pip install --no-cache-dir --force-reinstall "transformers>=5.4.0"
```

**3. Run the pipeline** (no extra flags needed — auto-detected):

```bash
python pipeline.py test_ocr.dcm
```

**Configuration via environment variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `LIGHTON_BASE_URL` | `http://localhost:8000/v1` | vLLM server URL |
| `LIGHTON_MODEL` | `lightonai/LightOnOCR` | Model name as served by vLLM |

Example pointing to a remote server:

```bash
export LIGHTON_BASE_URL=http://gpu-box:8000/v1
python pipeline.py test_ocr.dcm
```

## Adding a New Engine

1. Create `engines/yourengine.py` with a class that extends `OCREngine`
2. Implement `name`, `is_available()`, and `run(image, work_dir)`
3. Import and add to the `ENGINES` list in `engines/__init__.py`

See `engines/base.py` for the interface and any existing engine for a working example.

## Project Structure

| File | Purpose |
|------|---------|
| `pipeline.py` | Run all available engines, time each, compare metrics |
| `create_test_dicom.py` | Render a fake radiology report onto a DICOM image with scan noise |
| `check_ocr.py` | Check any OCR output against ground truth, report accuracy |
| `run-pipeline.sh` | Shell wrapper: generate DICOM then run pipeline |
| `dicom_utils.py` | Shared DICOM-to-PIL-Image conversion |
| `install.sh` | Set up virtualenv with dependencies |
| `engines/` | OCR engine plugins (Chandra, Tesseract, LightOn) |
| `engines/base.py` | `OCREngine` abstract base class |

## License

Chandra OCR 2 code is Apache 2.0. Model weights use a modified OpenRAIL-M license -- free for research, personal use, and startups under $2M revenue. Larger commercial use requires a [Datalab license](https://datalab.to).
