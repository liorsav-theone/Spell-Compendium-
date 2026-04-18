"""
This script can take a list of pdf of spells.
Sperate any multiple spells in the same pdf if any exists,
Create a webp for them
Update the spell.js with thier infomtion
To get the spell classes the sciprt search in the hwbrew spell json
"""
from pathlib   import Path
from PyPDFForm import PdfWrapper
import file_handler as fh
import fitz
from PIL import Image
import io
import re

# ─── CONFIG ───────────────────────────────────────────
SPELLS_OUT_DIR  = Path("spells")
SPELLS_JSON_DIR = Path("translation")
SPELLS_IN_DIR   = Path("spells_to_add")
IMAGES_DIR      = Path("images")
SPELLS_JS_PATH  = Path("data/spells.js")
WEBP_QUALITY    = 85
WEBP_DPI        = 200
# ──────────────────────────────────────────────────────
CLASSES = [
    "טרובדור", "כוהן", "דרואיד", "אביר קודש", "סייר", "אשף",
    "מכשף", "קוסם", "ממציא"
]

CLASS_MENU = "  ".join(f"[{i+1}]{c}" for i, c in enumerate(CLASSES))


def ask_classes(spell_name: str) -> list[str]:
    """Ask the user to pick classes for a spell."""
    return ["ממציא"]
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

def main():

    # Ensure output dirs exist
    SPELLS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    entries = []

    # Iterate over all spells to upload
    for input_path in SPELLS_IN_DIR.iterdir():

        # Read the spell
        spell = PdfWrapper(str(input_path))

        # Get spell data from the json (strip page suffix like " 1'" from multi-page spells)
        spell_name = spell.data['name'].replace(" 1'", "")
        spell_data = dict(spell.data)
        spell_data['classes'] = ask_classes(spell_name)

        # Open with fitz for image conversion (must reopen from bytes since PyPDFForm holds the stream)
        fitz_doc = fitz.open(stream=input_path.read_bytes(), filetype="pdf")

        # Save each page in a different file
        for page_index, page in enumerate(spell.pages):

            # Get page name
            page_name = next((v for k, v in page.data.items() if k == "name" or k.startswith('PName')), None)
            if page_name is None:
                raise ValueError(f'Could not find spell name on page {page_index} of {input_path.name}')

            # Save each page as a standalone PDF
            pdf_out = SPELLS_OUT_DIR / (page_name + '.pdf')
            page.write(str(pdf_out))

            # Create WebP image from the page
            img_out = IMAGES_DIR / (page_name + '.webp')
            zoom = WEBP_DPI / 72
            pix = fitz_doc[page_index].get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            img.save(str(img_out), "WEBP", quality=WEBP_QUALITY)

            # Collect entry for spells.js
            entries.append({
                "name":    page_name,
                "level":   int(spell_data.get('level', 0)),
                "school":  spell_data.get('school', ''),
                "classes": spell_data['classes'],
                "image":   f"images/{page_name}.webp",
                "pdf":     f"spells/{page_name}.pdf",
            })

            print(f"  ✓ {page_name}")

        fitz_doc.close()

    # Write all entries to spells.js
    if entries:
        append_to_spells_js(entries)


# If you know you know ;)
if __name__ == "__main__":
    main()
