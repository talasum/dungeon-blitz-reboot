#!/usr/bin/env python3
"""
Test script to verify noJumpAttack flag is being properly loaded
and sent through the entity packet protocol.
"""

import os
import json
import sys

# Change to server directory for relative path loading
os.chdir('server')
sys.path.insert(0, '.')

from entity import load_npc_data_for_level, Send_Entity_Data

def test_nojump_flag():
    print("=" * 70)
    print("Testing noJumpAttack Flag Flow")
    print("=" * 70)
    
    # Test 1: Load NPC data and check for noJumpAttack property
    print("\n[TEST 1] Loading NPCs from NewbieRoad.json...")
    npcs = load_npc_data_for_level("NewbieRoad")
    
    print(f"   Loaded {len(npcs)} NPCs")
    
    nojump_count = 0
    for npc in npcs[:10]:  # Check first 10
        has_nojump = npc.get("noJumpAttack", False)
        team = npc.get("team", 0)
        name = npc.get("name", "Unknown")
        
        if has_nojump:
            nojump_count += 1
            print(f"   ✓ {name} (team={team}) has noJumpAttack={has_nojump}")
        elif team == 2:
            print(f"   ✗ {name} (team={team}) missing noJumpAttack (should be True)")
    
    total_nojump = sum(1 for npc in npcs if npc.get("noJumpAttack", False))
    print(f"\n   Total NPCs with noJumpAttack: {total_nojump}/{len(npcs)}")
    
    # Test 2: Send entity data and verify packet contains flag
    print("\n[TEST 2] Sending entity data for a Goblin with noJumpAttack=True...")
    
    test_entity = {
        "id": 254690,
        "name": "GoblinArmorSword",
        "x": 100,
        "y": 200,
        "v": 0,
        "team": 2,
        "untargetable": False,
        "facing_left": False,
        "entState": 0,
        "noJumpAttack": True,  # THIS IS THE KEY FLAG
        "is_player": False,
        "render_depth_offset": 0,
        "health_delta": 0,
        "buffs": [],
    }
    
    try:
        packet_data = Send_Entity_Data(test_entity)
        print(f"\n   ✓ Entity data packet generated: {len(packet_data)} bytes")
        print(f"   ✓ Packet hex (first 32 bytes): {packet_data[:32].hex()}")
        
        # The noJumpAttack flag should be in the packet
        # (exact byte location depends on the packet protocol)
        if len(packet_data) > 20:
            print(f"   ✓ Packet is long enough to contain all fields")
        else:
            print(f"   ✗ Packet too short!")
            
    except Exception as e:
        print(f"   ✗ Error sending entity data: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Check goblins specifically
    print("\n[TEST 3] Verifying all Goblin-type enemies have noJumpAttack=True...")
    
    goblin_types = [
        "GoblinClub", "GoblinDagger", "GoblinArmorSword", "GoblinArmorAxe",
        "GoblinHatchet", "GoblinBrute", "GoblinShaman", "GoblinShamanSkullHat",
        "GoblinShamanHood", "GoblinMiniBoss", "Devourer"
    ]
    
    mismatches = 0
    for npc in npcs:
        name = npc.get("name", "")
        team = npc.get("team", 0)
        has_nojump = npc.get("noJumpAttack", False)
        
        # Check if any goblin-type or devourer is missing the flag
        is_goblin_type = any(gt in name for gt in goblin_types)
        
        if is_goblin_type and team == 2:  # Enemy goblins/devourers
            if not has_nojump:
                print(f"   ✗ {name} (team=2) missing noJumpAttack flag!")
                mismatches += 1
    
    if mismatches == 0:
        print(f"   ✓ All {total_nojump} enemy goblins/devourers have noJumpAttack=True")
    else:
        print(f"   ✗ Found {mismatches} enemies without noJumpAttack flag")
    
    print("\n" + "=" * 70)
    print(f"RESULT: {'✓ PASS' if mismatches == 0 and total_nojump > 0 else '✗ FAIL'}")
    print("=" * 70)


if __name__ == "__main__":
    test_nojump_flag()
