"""
Open files and return them as python objects
"""
import re
from pathlib import Path
import json

def process_spell(spell:str) -> dict:
    """Process a spell in a string form into dict"""

    # Declare empty dict
    spell_dict = {}

    # Split into header, attr, and description
    header, body = spell.split('___')
    attr, desc = body.split('\n---\n')

    # Process header
    header_pattern = r"#### (.+)\n\*Level ([1-9]) (\w+)\*"
    match = re.search(header_pattern, header)
    if not match:
        raise ValueError(f"invalid spell header - {header} - could not process the header structer.")
    spell_dict['name'], spell_dict['level'], spell_dict['school'] = match.groups()

    # Process attributes
    attr_pattern = r"\n- \*\*Casting Time:\*\* (.+)\n- \*\*Range:\*\* (.+)\n- \*\*Components:\*\* (.+)\n- \*\*Duration:\*\* (.+)"
    match = re.search(attr_pattern, attr)
    if not match:
        raise ValueError(f"invalid spell attributes - {attr} - could not process the header attirbute.")
    spell_dict['casting_time'], spell_dict['range'], spell_dict['components'], spell_dict['duration'] = match.groups()

    # No need to process description
    spell_dict['desc'], spell_dict['classes'] = desc.split('\n\n**Classes:** ')

    # Add empty saving throw key 
    spell_dict['saving_throw'] = ""

    # TODO: if the  spell_dict['components'] string has a '(' and a ')'
    if "M" in spell_dict["components"]:
        find_result = spell_dict["components"].find('(')
        spell_dict['mcomponents'] = spell_dict["components"][find_result+1:-1]
        spell_dict["components"]  = spell_dict["components"][:find_result-1]

    # Return the new dict
    return spell_dict

def process_md(file_path: Path) -> list[dict]:
    "Reads a markdown spell list and convert it into lists of dict"
    
    # Read the spells from the file and split into individual spells
    spells = file_path.read_text().split("\n\n---\n\n")

    # Process each spell into dict
    spells = [process_spell(spell) for spell in spells]

    # Return the spells
    return spells

def process_json(file_path: Path) -> list[dict]:
    return json.loads(file_path.read_text(encoding="utf-8"))


def open(file_path: Path) -> list[dict]:
    if file_path.suffix == ".md":
        process = process_md
    elif file_path.suffix == ".json":
        process = process_json
    else:
        raise ValueError(f"File suffix - {file_path.suffix} - is unknown.")

    return process(file_path)

def write(data: list[dict], path: Path) -> None:
    print(f"Output written to: {path}")
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent="\t")
