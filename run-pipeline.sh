#!/usr/bin/env bash
# Run the full Phantom Glyphs pipeline: generate test DICOM, run OCR, report results.
# bash run-pipeline.sh                # default HuggingFace backend
# bash run-pipeline.sh --method vllm  # vLLM server backend

set -euo pipefail

readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly RESET='\033[0m'

readonly DICOM_FILE="test_ocr.dcm"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

info()  { printf "${CYAN}[INFO]${RESET}  %s\n" "$1"; }
ok()    { printf "${GREEN}[OK]${RESET}    %s\n" "$1"; }
warn()  { printf "${YELLOW}[WARN]${RESET}  %s\n" "$1"; }
error() { printf "${RED}[ERROR]${RESET} %s\n" "$1" >&2; }

usage() {
    cat <<EOF
Usage: $(basename "$0") [--method hf|vllm] [--help]

Options:
  --method   OCR backend: hf (default) or vllm
  --help     Show this help
EOF
}

# Parse arguments
parse_args() {
    local method="hf"
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --method)
                method="${2:?--method requires a value (hf or vllm)}"
                shift 2
                ;;
            --help|-h)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
    echo "${method}"
}

# Verify Python and venv are available
check_environment() {
    if [[ ! -d "${SCRIPT_DIR}/.venv" ]]; then
        error "Virtual environment not found. Run install.sh first."
        exit 1
    fi

    # shellcheck disable=SC1091
    source "${SCRIPT_DIR}/.venv/bin/activate"
    info "Activated venv: ${VIRTUAL_ENV}"
}

# Step 1: Generate test DICOM
generate_dicom() {
    printf "\n${BOLD}=== Step 1: Generate Test DICOM ===${RESET}\n"
    info "Creating DICOM with confusable glyphs..."

    python "${SCRIPT_DIR}/create_test_dicom.py" "${DICOM_FILE}"

    if [[ -f "${DICOM_FILE}" ]]; then
        ok "DICOM created: ${DICOM_FILE}"
    else
        error "DICOM generation failed"
        exit 1
    fi

    local preview="${DICOM_FILE%.dcm}_preview.png"
    if [[ -f "${preview}" ]]; then
        ok "Preview saved: ${preview}"
    fi
}

# Step 2: Run OCR
run_ocr() {
    local method="$1"
    printf "\n${BOLD}=== Step 2: Run Chandra OCR (${method}) ===${RESET}\n"
    info "Processing ${DICOM_FILE}..."

    python "${SCRIPT_DIR}/run_ocr.py" "${DICOM_FILE}" --method "${method}"

    local output_md="${DICOM_FILE%.dcm}_ocr_output.md"
    if [[ -f "${output_md}" ]]; then
        ok "OCR output saved: ${output_md}"
    else
        warn "No output file found"
    fi
}

# Step 3: Check Chandra accuracy against ground truth
check_chandra() {
    local output_md="${DICOM_FILE%.dcm}_ocr_output.md"
    printf "\n${BOLD}=== Step 3: Check Chandra Accuracy ===${RESET}\n"

    if [[ ! -f "${output_md}" ]]; then
        warn "No Chandra output to check (${output_md} missing)"
        return 1
    fi

    python "${SCRIPT_DIR}/check_ocr.py" "${output_md}"
}

# Step 4: Run Tesseract OCR + check accuracy
run_tesseract() {
    printf "\n${BOLD}=== Step 4: Run Tesseract OCR ===${RESET}\n"

    if ! python -c "import pytesseract" 2>/dev/null; then
        warn "pytesseract not installed — skipping Tesseract step"
        return 1
    fi

    if ! command -v tesseract &>/dev/null; then
        warn "tesseract binary not found — install with: sudo apt install tesseract-ocr"
        return 1
    fi

    info "Processing ${DICOM_FILE} with Tesseract..."
    python "${SCRIPT_DIR}/tesseract_check.py" "${DICOM_FILE}"

    local output_md="${DICOM_FILE%.dcm}_tesseract_output.md"
    if [[ -f "${output_md}" ]]; then
        ok "Tesseract output saved: ${output_md}"
    else
        warn "No Tesseract output file found"
    fi
}

# Step 5: Compare engines
compare_engines() {
    local chandra_md="${DICOM_FILE%.dcm}_ocr_output.md"
    local tesseract_md="${DICOM_FILE%.dcm}_tesseract_output.md"
    printf "\n${BOLD}=== Step 5: Compare Chandra vs Tesseract ===${RESET}\n"

    if [[ ! -f "${chandra_md}" ]]; then
        warn "Chandra output missing — cannot compare"
        return 1
    fi
    if [[ ! -f "${tesseract_md}" ]]; then
        warn "Tesseract output missing — cannot compare"
        return 1
    fi

    python "${SCRIPT_DIR}/compare_ocr.py" "${chandra_md}" "${tesseract_md}"
}

# Summary
print_summary() {
    printf "\n${BOLD}=== Pipeline Complete ===${RESET}\n"
    ok "Generated files:"
    local files=(
        "${DICOM_FILE}"
        "${DICOM_FILE%.dcm}_preview.png"
        "${DICOM_FILE%.dcm}_ocr_output.md"
        "${DICOM_FILE%.dcm}_tesseract_output.md"
    )
    for file in "${files[@]}"; do
        if [[ -f "${file}" ]]; then
            printf "  ${GREEN}✔${RESET} %s\n" "${file}"
        else
            printf "  ${RED}✘${RESET} %s\n" "${file}"
        fi
    done
}

main() {
    local method
    method=$(parse_args "$@")

    printf "${BOLD}${CYAN}Phantom Glyphs — OCR Stress Test Pipeline${RESET}\n"

    check_environment
    generate_dicom
    run_ocr "${method}"
    check_chandra
    run_tesseract || true
    compare_engines || true
    print_summary
}

main "$@"
