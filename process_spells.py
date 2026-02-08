#!/usr/bin/env python3
"""
Spell Card Processor
====================
Takes a PDF with one spell per page. For each page:
  1. Extracts Name, School, Level from PDF form fields
  2. Saves the page as a standalone PDF in spells/
  3. Exports the page as WebP image in images/
  4. Asks you for the spell's classes
  5. Appends the spell entry to data/spells.js

Usage:
  python process_spells.py path/to/spells.pdf

Prerequisites:
  pip install pypdf PyMuPDF Pillow
"""

import sys
import os
import re
from pathlib import Path
from pypdf import PdfReader
import fitz  # PyMuPDF
from PIL import Image
import io
import argparse

# ─── CONFIG ───────────────────────────────────────────
SPELLS_PDF_DIR = "spells"
IMAGES_DIR = "images"
HIRES_DIR = "high_res_images"
SPELLS_JS_PATH = "data/spells.js"
WEBP_QUALITY = 85       # WebP quality (1-100)
WEBP_DPI = 200          # Resolution for PDF→image conversion
HIRES_DPI = 600         # Resolution for high-res print PNG
# ──────────────────────────────────────────────────────

CLASSES = [
    "Barbarian", "Bard", "Cleric", "Druid", "Fighter",
    "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer",
    "Warlock", "Wizard", "Artificer"
]

CLASS_MENU = "  ".join(f"[{i+1}]{c}" for i, c in enumerate(CLASSES))


def slugify(name: str) -> str:
    """Convert spell name to a filename-safe slug."""
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s]+", "-", s)
    return s


def get_form_field(page, prefix: str) -> str:
    """
    Find a form field whose name starts with prefix (e.g. 'Name_').
    Ignores random trailing characters like 'Name_F00'.
    Returns the field value or None.
    """
    fields = page.get("/Annots")
    if not fields:
        return None
    for annot_ref in fields:
        annot = annot_ref.get_object()
        field_name = annot.get("/T", "")
        if not field_name and annot.get("/Parent"):
            parent = annot["/Parent"].get_object()
            field_name = parent.get("/T")
        if isinstance(field_name, str) and field_name.startswith(prefix):
            # Try /V first (value), then /AS (appearance state)
            val = annot.get("/V")
            if (not val) and annot.get("/Parent"):
                parent = annot["/Parent"].get_object()
                val = parent.get("/V")
            if val is not None:
                return str(val).strip()
    return None


def ask_classes(spell_name: str) -> list[str]:
    """Ask the user to pick classes for a spell."""
    print(f"\n  📜 {spell_name[::-1]}")
    print(f"  {CLASS_MENU}")
    raw = input("  Classes (numbers, e.g. 10 12): ").strip()

    if not raw:
        return []

    indices = re.findall(r"\d+", raw)
    selected = []
    for idx_str in indices:
        idx = int(idx_str) - 1
        if 0 <= idx < len(CLASSES):
            selected.append(CLASSES[idx])

    print(f"  → {', '.join(selected)}")
    return selected


def append_to_spells_js(entries: list[dict]):
    """Append spell entries to data/spells.js before the closing '];'."""
    js_path = Path(SPELLS_JS_PATH)

    if not js_path.exists():
        print(f"  ⚠ {SPELLS_JS_PATH} not found. Creating it.")
        js_path.parent.mkdir(parents=True, exist_ok=True)
        js_path.write_text("const SPELLS = [\n];\n", encoding="utf-8")

    content = js_path.read_text(encoding="utf-8")

    # Build JS lines for each spell
    new_lines = []
    for e in entries:
        classes_str = ", ".join(f'"{c}"' for c in e["classes"])
        line = (
            f'  {{ name: "{e["name"]}", '
            f'level: {e["level"]}, '
            f'school: "{e["school"]}", '
            f'classes: [{classes_str}], '
            f'image: "{e["image"]}", '
            f'pdf: "{e["pdf"]}" }},'
        )
        new_lines.append(line)

    insert_text = "\n".join(new_lines) + "\n"

    # Insert before the last "];"
    pos = content.rfind("];")
    if pos == -1:
        print("  ❌ Could not find '];\\ in spells.js")
        return

    new_content = content[:pos] + insert_text + content[pos:]
    js_path.write_text(new_content, encoding="utf-8")
    print(f"\n  ✅ Added {len(entries)} spells to {SPELLS_JS_PATH}")


if __name__ == "__main__":
    
    # Declare the argparser
    parser = argparse.ArgumentParser(description="Extract spell cards from a given pdf.")
    parser.add_argument("path", type=Path, help="Path to the input pdf file")
    args = parser.parse_args()

    # Check the path exists
    if not args.path.exists():
        print(f"❌ File not found: {args.path}")
        sys.exit(1)

    #  Open the file
    reader = PdfReader(args.path)
    print(f"\n🔮 Processing {args.path.name} — {len(reader.pages)} pages\n")

    # Open with PyMuPDF for image conversion
    fitz_doc = fitz.open(args.path)

    Path(HIRES_DIR).mkdir(parents=True, exist_ok=True)

    entries = []
    skipped = 0
    level = 0
    school= ""
    classes = []

    for i, page in enumerate(reader.pages):
        page_num = i + 1

        # ── Extract form fields ──
        name = get_form_field(page, "Name_")
        pname = get_form_field(page, "PName_")
        if not pname:
            school = get_form_field(page, "School_")
            level = get_form_field(page, "Level_")
        else:
            name=pname

        if not (name or pname):
            print(f"  ⚠ Page {page_num}: No 'Name_' field found — skipping")
            skipped += 1
            continue

        level  = int(level)
        school = school or "Unknown"
        slug   = name

        # ── Save single-page PDF (rasterised at 300 DPI to bake in form fields) ──
        pdf_out = f"{SPELLS_PDF_DIR}/{slug}.pdf"
        page_rect = fitz_doc[i].rect
        hires = fitz_doc[i].get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
        single = fitz.open()
        pg = single.new_page(width=page_rect.width, height=page_rect.height)
        pg.insert_image(pg.rect, pixmap=hires)
        single.save(pdf_out, deflate=True)
        single.close()

        # ── Save WebP image ──
        img_out = f"{IMAGES_DIR}/{slug}.webp"
        zoom = WEBP_DPI / 72  # 72 is PDF default DPI
        mat = fitz.Matrix(zoom, zoom)
        pix = fitz_doc[i].get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        img.save(img_out, "WEBP", quality=WEBP_QUALITY)

        # ── Save high-res PNG (from original vector source) ──
        hires_out = f"{HIRES_DIR}/{slug}.png"
        hires_zoom = HIRES_DPI / 72
        hires_mat = fitz.Matrix(hires_zoom, hires_zoom)
        hires_pix = fitz_doc[i].get_pixmap(matrix=hires_mat)
        hires_pix.save(hires_out)

        # ── Ask for classes ──
        if not pname:
            classes = ask_classes(name)

        entries.append({
            "name": name,
            "level": level,
            "school": school,
            "classes": classes,
            "image": img_out,
            "pdf": pdf_out,
        })

        print(f"  ✓ [{page_num}] {name}")

    # ── Clean up ──
    fitz_doc.close()

    # ── Write to spells.js ──
    if entries:
        append_to_spells_js(entries)

    print(f"\n🏁 Done! {len(entries)} spells processed, {skipped} skipped.\n")
