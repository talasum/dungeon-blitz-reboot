#!/usr/bin/env python3
"""
Fix jump attacks during monster combat on NewbieRoad and goblin dungeons.
This script adds "noJumpAttack": true to all monsters on NewbieRoad
and goblin-containing dungeons.
"""

import json
import os
from pathlib import Path

# Define which monsters and dungeons to fix
NEWBIEROAD_FILE = "server/world_npcs/NewbieRoad.json"
GOBLIN_DUNGEON_FILES = [
    "server/world_npcs/GoblinRiverDungeon.json",
    "server/world_npcs/TutorialDungeon.json",  # Contains goblins
]

# Combat-related entity types that should not jump while attacking
NO_JUMP_ENTITIES = {
    # Goblins
    "Goblin", "GoblinClub", "GoblinDagger", "GoblinArmorSword", "GoblinArmorAxe",
    "GoblinHatchet", "GoblinBrute", "GoblinShaman", "GoblinShamanSkullHat", "GoblinShamanHood",
    "GoblinMiniBoss", "IntroGoblin",
    # Devourers
    "Devourer",
    # Other aggressive monsters
}

def should_disable_jump(entity_name):
    """Check if entity should have jump attacks disabled."""
    if not entity_name:
        return False
    
    # Check if name contains any of the no-jump entities
    for no_jump_ent in NO_JUMP_ENTITIES:
        if no_jump_ent.lower() in entity_name.lower():
            return True
    
    return False

def fix_json_file(file_path, is_newbieroad=False):
    """Add noJumpAttack property to monster entities in a JSON file."""
    if not os.path.exists(file_path):
        print(f"  ✗ File not found: {file_path}")
        return 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        print(f"  ✗ Invalid format (not a list): {file_path}")
        return 0
    
    modified_count = 0
    for entity in data:
        if not isinstance(entity, dict):
            continue
        
        entity_name = entity.get("name", "")
        
        # For NewbieRoad, disable jump for ALL monsters (team 2 = enemies)
        if is_newbieroad:
            team = entity.get("team")
            # Skip NPCs and friendlies
            if team == 2:  # Enemy team
                if entity_name and not entity_name.startswith("NPC"):
                    if "noJumpAttack" not in entity:
                        entity["noJumpAttack"] = True
                        modified_count += 1
                        print(f"    ✓ {entity_name} (ID: {entity.get('id')})")
        else:
            # For dungeons, disable jump for specific monster types only
            if should_disable_jump(entity_name):
                if "noJumpAttack" not in entity:
                    entity["noJumpAttack"] = True
                    modified_count += 1
                    print(f"    ✓ {entity_name} (ID: {entity.get('id')})")
    
    # Write back
    if modified_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  → Saved {modified_count} changes to {file_path}")
    else:
        print(f"  → No changes needed for {file_path}")
    
    return modified_count

def main():
    print("=" * 70)
    print("FIXING JUMP ATTACKS IN COMBAT")
    print("=" * 70)
    
    total_modified = 0
    
    # Fix NewbieRoad
    print("\n[1/3] Processing NewbieRoad.json...")
    modified = fix_json_file(NEWBIEROAD_FILE, is_newbieroad=True)
    total_modified += modified
    
    # Fix goblin dungeons
    for dungeon_file in GOBLIN_DUNGEON_FILES:
        print(f"\n[*] Processing {Path(dungeon_file).name}...")
        modified = fix_json_file(dungeon_file, is_newbieroad=False)
        total_modified += modified
    
    print("\n" + "=" * 70)
    print(f"✓ COMPLETE: Modified {total_modified} entity instances")
    print("=" * 70)
    print("\nChanges applied:")
    print("  • NewbieRoad: All monsters can't jump while attacking")
    print("  • Dungeons: Goblin and devourer types can't jump while attacking")
    print("\nNote: The 'noJumpAttack' flag will be checked by the Flash client")
    print("      during animation playback.")

if __name__ == "__main__":
    main()
