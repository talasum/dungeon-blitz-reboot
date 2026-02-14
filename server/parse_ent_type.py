import re
import json
import os
import xml.etree.ElementTree as ET

INPUT_FILE = "../extra-modules/swz-scripts/Login.swz.txt"
OUTPUT_FILE = "data/EntTypes.json"

def parse():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    print(f"Reading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Find the EntTypes XML block
    start_tag = '<EntTypes'
    end_tag = '</EntTypes>'
    
    start_idx = content.find(start_tag)
    end_idx = content.find(end_tag)
    
    if start_idx == -1 or end_idx == -1:
        print("Error: Could not find <EntTypes> block.")
        return

    xml_content = content[start_idx : end_idx + len(end_tag)]
    
    # Fix potential XML issues if any (e.g. & encoded chars)
    # The file seems to be a text dump, hopefully valid XML.
    
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
        # Fallback: Try identifying line number and context
        return

    ent_types_list = []
    
    print(f"Found {len(root)} entries. Processing...")
    
    count = 0
    for child in root:
        if child.tag != "EntType":
            continue
            
        ent_data = child.attrib.copy() # EntName, parent
        
        # Parse children as properties
        for prop in child:
            # Handle list-like strings or sub-objects if necessary
            # For now, we take text content.
            # Some props like <EquippedGear> have sub-children.
            if len(prop) > 0:
                # Has children (e.g. EquippedGear)
                # We can store it as a dict or just skip for now if not needed for Loot.
                # Loot needs: GoldDrop, ItemDropChance, EntRank. These are simple tags.
                # BUT, let's try to capture simple dicts for deeper structure if needed.
                pass 
            
            if prop.text and prop.text.strip():
                ent_data[prop.tag] = prop.text.strip()
        
        ent_types_list.append(ent_data)
        count += 1

    # Output structure
    output_data = {
        "EntTypes": {
            "EntType": ent_types_list
        }
    }
    
    print(f"Writing {count} EntTypes to {OUTPUT_FILE}...")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    print("Done.")

if __name__ == "__main__":
    parse()
