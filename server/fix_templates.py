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
        
    # Fresh characters should start on the ship with mission 1 active.
    data["CurrentLevel"] = {"name": "TutorialBoat", "x": 0, "y": 0}
    data["PreviousLevel"] = {"name": "NewbieRoad", "x": 1422, "y": 827}
    data["missions"] = {
        "1": {
            "state": 1,
            "currCount": 0
        }
    }
    
    with open(tpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        
    print(f"Updated {tpath}")
