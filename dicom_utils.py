#!/usr/bin/env python3
"""Shared DICOM-to-image conversion."""

import numpy as np
import pydicom
from PIL import Image


def dicom_to_image(dicom_path):
    """Extract pixel data from a DICOM file and return a PIL Image."""
    ds = pydicom.dcmread(dicom_path)
    pixels = ds.pixel_array

    if pixels.dtype != np.uint8:
        pmin, pmax = float(pixels.min()), float(pixels.max())
        if pmax > pmin:
            pixels = ((pixels - pmin) / (pmax - pmin) * 255).astype(np.uint8)
        else:
            pixels = np.zeros_like(pixels, dtype=np.uint8)

    return Image.fromarray(pixels)
