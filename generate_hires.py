#!/usr/bin/env python3
"""
High-Res PNG Generator
========================
Iterates over all PDFs in spells/ and creates high-resolution
lossless PNG images in high_res_images/ for print-quality output.

Usage:
  python generate_hires.py

Prerequisites:
  pip install PyMuPDF
"""

from pathlib import Path
import fitz  # PyMuPDF

# ─── CONFIG ───────────────────────────────────────────
SPELLS_PDF_DIR = "spells"
HIRES_DIR = "high_res_images"
DPI = 600
# ──────────────────────────────────────────────────────

def main():
    pdf_dir = Path(SPELLS_PDF_DIR)
    out_dir = Path(HIRES_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {SPELLS_PDF_DIR}/")
        return

    print(f"\nGenerating {DPI} DPI lossless PNG for {len(pdfs)} spell PDFs\n")

    for i, pdf_path in enumerate(pdfs, 1):
        stem = pdf_path.stem
        out_path = out_dir / f"{stem}.png"

        doc = fitz.open(pdf_path)
        page = doc[0]
        zoom = DPI / 72
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        pix.save(str(out_path))
        doc.close()

        print(f"  [{i}/{len(pdfs)}] {stem}.png")

    print(f"\nDone! {len(pdfs)} high-res PNG images saved to {HIRES_DIR}/\n")


if __name__ == "__main__":
    main()
