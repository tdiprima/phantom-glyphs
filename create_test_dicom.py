#!/usr/bin/env python3
"""Create a DICOM image containing text with easily confused characters for OCR testing.

Renders a fake radiology report where visually similar characters appear in
context: S/$, 0/O, 1/l/I, 5/S, 8/B, Z/2. The image includes light scan
noise to simulate a real-world scanned document.
"""

import datetime
import os
import sys

import numpy as np
import pydicom
import pydicom.uid
from PIL import Image, ImageDraw, ImageFont
from pydicom.dataset import FileDataset
from pydicom.uid import ExplicitVRLittleEndian

REPORT_TEXT = """\
RADIOLOGY REPORT
================================

Patient: SOLOMON O'BRIEN         MRN: OI01l0II01
DOB: 01/08/1962                  DOS: 05/12/2026
Acct#: $5,250.00                 Status: OUTPATIENT

CLINICAL HISTORY:
58-year-old male with SOB. Insurance copay $500.
Prior CT scan (01/01/2026) showed 3mm nodule in S5.

TECHNIQUE:
PA and lateral chest radiograph. kVp: 110, mAs: 5.0

COMPARISON: 01/01/2026

FINDINGS:
1. Solitary 5mm pulmonary nodule in segment S5 of
   the right upper lobe. Previously 3mm (01/01/2026).
   Interval growth: 0.2cm over 5 months.

2. Bilateral pleural effusions.
   Right: moderate (~500mL estimated).
   Left: mild (~100mL estimated).

3. Cardiac silhouette is normal in size.
   Cardiothoracic ratio: 0.51 (normal <0.50).
   Aortic calcification: Grade II.

4. Osseous structures: Old fracture rib #8 right.
   Bone mineral density Z-score: -2.1.
   DEXA recommended for osteoporosis screening.

5. Soft tissues: Bilateral axillary lymph nodes,
   largest 1.1cm. Likely benign (morphologically
   normal appearance).

IMPRESSION:
- 5mm RUL nodule, interval growth from 3mm.
  Recommend CT chest in 6-8 weeks. [Lung-RADS 3]
- Bilateral pleural effusions, clinical correlation.
  Estimate: R ~500mL, L ~100mL.
- Borderline cardiomegaly (ratio 0.51).
- Old rib fracture #8. Z-score -2.1.

BILLING: CPT 71046 -- $1,250.00
         Professional fee: $350.00
         Total charges: $1,600.00

Dictated by: Dr. Claire I. Bennett, MD
Badge: B8B88b     Employee ID: Il1O0oO01l
Signed electronically: 05/12/2026 15:08:51
"""

CONFUSING_PAIRS = [
    ("S vs $", "SOLOMON, SOB, S5 vs $500, $5,250, $1,250"),
    ("0 vs O", "O'BRIEN, SOLOMON, OI01l0II01, 0.2cm, 0.51"),
    ("1 vs l vs I", "Il1O0oO01l, 1.1cm, Claire I., MRN field"),
    ("5 vs S", "S5 segment, 5mm, 58-year-old, $5,250"),
    ("8 vs B", "B8B88b badge, rib #8, 6-8 weeks"),
    ("Z vs 2", "Z-score vs -2.1"),
]


def find_font(size):
    """Find a sans-serif font where similar characters are hardest to distinguish."""
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSText.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Geneva.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except (IOError, OSError):
                continue
    return ImageFont.load_default()


def render_text_to_image(text, width=1400, font_size=18):
    """Render text onto a grayscale image with simulated scan noise."""
    font = find_font(font_size)
    lines = text.split("\n")
    line_height = font_size + 6
    height = len(lines) * line_height + 120

    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)

    y_pos = 50
    for line in lines:
        draw.text((60, y_pos), line, fill=15, font=font)
        y_pos += line_height

    pixels = np.array(img, dtype=np.float32)
    noise = np.random.default_rng(42).normal(0, 3, pixels.shape)
    pixels = np.clip(pixels + noise, 0, 255).astype(np.uint8)

    return Image.fromarray(pixels)


def create_dicom(image, output_path):
    """Wrap a grayscale PIL image into a DICOM Secondary Capture file."""
    pixel_array = np.array(image)

    file_meta = pydicom.Dataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.7"
    file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = FileDataset(output_path, {}, file_meta=file_meta, preamble=b"\x00" * 128)

    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = pydicom.uid.generate_uid()
    ds.SeriesInstanceUID = pydicom.uid.generate_uid()
    ds.FrameOfReferenceUID = pydicom.uid.generate_uid()

    ds.Modality = "OT"
    ds.Manufacturer = "OCR Test Generator"
    ds.PatientName = "SOLOMON^OBRIEN"
    ds.PatientID = "OI01l0II01"

    now = datetime.datetime.now()
    ds.StudyDate = now.strftime("%Y%m%d")
    ds.ContentDate = now.strftime("%Y%m%d")
    ds.StudyTime = now.strftime("%H%M%S")
    ds.ContentTime = now.strftime("%H%M%S")

    ds.Rows, ds.Columns = pixel_array.shape
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelRepresentation = 0
    ds.PixelData = pixel_array.tobytes()

    ds.save_as(output_path)


def main():
    output_path = sys.argv[1] if len(sys.argv) > 1 else "test_ocr.dcm"

    print("Rendering confusing text to image...")
    image = render_text_to_image(REPORT_TEXT)

    png_path = output_path.replace(".dcm", "_preview.png")
    image.save(png_path)
    print(f"Preview saved: {png_path}")

    print(f"Creating DICOM: {output_path}")
    create_dicom(image, output_path)
    print("Done.\n")

    print("Confusing character pairs in this image:")
    for pair, examples in CONFUSING_PAIRS:
        print(f"  {pair:14s} | {examples}")


if __name__ == "__main__":
    main()
