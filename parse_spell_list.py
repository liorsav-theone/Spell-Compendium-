"""
Parse spell lists files doing data manipulation on the spells to convert them between formats 
"""
from   pathlib import Path
import file_handler as fh
import pdf_spell_maker as pdfh

FILE_PATH = Path("translation/hebrew_1.json")
# FILE_PATH = Path("spell_lists.md")
OUTPUT_FILE_PATH = Path("output") / Path("spell_for_trasnlation.json")
MAX_SPELLS_PER_JSON = 10

def md_to_json(data: list[dict]) -> None:
  
    # Split into multiple chunks
    if MAX_SPELLS_PER_JSON:
        data_chunks = [data[i:i + MAX_SPELLS_PER_JSON] for i in range(0, len(data), MAX_SPELLS_PER_JSON)]
    else:
        data_chunks = [data]

    # Write the output
    for index, value in enumerate(data_chunks):
        fh.write(value, OUTPUT_FILE_PATH.with_name(f"{OUTPUT_FILE_PATH.stem}_{index}{OUTPUT_FILE_PATH.suffix}"))

def json_to_pdf(data: list[dict]) -> None:
  
    # Conecrt every spell into pdf
    for spell in data:
        pdfh.convert_to(spell)

def main():
    folder_path = Path('translation')
    for file in folder_path.iterdir():
        data= fh.open(file)
        json_to_pdf(data) 
    exit(0)
    # Open the file 
    data = fh.open(FILE_PATH)

    # markdwon -> json
    if FILE_PATH.suffix == '.md':
        md_to_json(data)
    
    # Json to PDF 
    elif FILE_PATH.suffix == '.json':
        json_to_pdf(data) 

# If you know you know ;)
if __name__ == "__main__": 
    main()