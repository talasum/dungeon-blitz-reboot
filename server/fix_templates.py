import json
import os

TEMPLATES = [
    "data/mage_template.json",
    "data/paladin_template.json",
    "data/rogue_template.json"
]

for tpath in TEMPLATES:
    if not os.path.exists(tpath):
        continue
    with open(tpath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Overwrite the entire missions dictionary to reset the character's quest progress
    data["missions"] = {
        "1": {
            "state": 2,          # Completed
            "currCount": 1,
            "Tier": 10,
            "highscore": 99999999,
            "Time": 1710000000
        },
        "2": {
            "state": 1,          # In Progress! This actively assigns the mission.
            "currCount": 0
        }
    }
    
    with open(tpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        
    print(f"Updated {tpath}")
