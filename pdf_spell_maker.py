from pathlib   import Path
from PyPDFForm import PdfWrapper

# ─── CONFIG ───────────────────────────────────────────
SPELLS_PDF_DIR = Path("process")
IMAGES_DIR     = Path("images")
SPELLS_JS_PATH = Path("data/spells.js")
WEBP_QUALITY   = 85  # WebP quality (1-100)
WEBP_DPI       = 200 # Resolution for PDF→image conversion
SPELL_TEMPLATE_WITH_PYSHICAL_COMPONENTS    = Path("assets/Spell Cards Hebrew With Pyshical Components.pdf")
SPELL_TEMPLATE_WITHOUT_PYSHICAL_COMPONENTS = Path("assets/Spell Cards Hebrew.pdf")
# ──────────────────────────────────────────────────────

def convert_to(spell: dict) -> None:
    """Convert a given spell dict into pdf"""

    # Open the correct pdf according to the components
    if "mcomponents" in spell:
        pdf_tample = SPELL_TEMPLATE_WITH_PYSHICAL_COMPONENTS 
    else:
        pdf_tample = SPELL_TEMPLATE_WITHOUT_PYSHICAL_COMPONENTS

    # Fill the forms
    filled = PdfWrapper(str(pdf_tample), need_appearances=True).fill(spell)

    # Save the pdf
    output_path = SPELLS_PDF_DIR / f"{spell['name']}.pdf"
    if output_path.is_file():
        print(f"existing file {output_path}")
    filled.write(str(output_path))
