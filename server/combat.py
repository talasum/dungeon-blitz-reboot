import struct
import time

from BitBuffer import BitBuffer
from accounts import save_characters
from bitreader import BitReader
from constants import Entity, PowerType, GearType, class_64, class_1, EntType, class_21, Game
from globals import (
    send_consumable_update,
    build_change_offset_y_packet,
    GS,
    send_xp_reward,
    send_hp_update,
    send_quest_progress,
    record_dungeon_kill,
    get_npc_props,
    XP_CAP_PER_KILL,
    send_pet_xp_update,
)
from level_config import LEVEL_CONFIG


                # Helpers
    #####################################

def get_base_hp_for_level(level):
    if level < 1:
        level = 1
    if level >= len(Entity.PLAYER_HITPOINTS):
        level = len(Entity.PLAYER_HITPOINTS) - 1
    return Entity.PLAYER_HITPOINTS[level]

def write_enttype_gear(bb, gear):
    """
    gear dict format:
    {
        gearID, tier,
        rune1, rune2, rune3,
        color1, color2
    }
    """
    bb.write_method_6(gear["gearID"], GearType.GEARTYPE_BITSTOSEND)
    bb.write_method_6(gear["tier"], GearType.const_176)

    runes = gear.get("runes")
    if isinstance(runes, (list, tuple)) and len(runes) >= 3:
        rune1 = int(runes[0])
        rune2 = int(runes[1])
        rune3 = int(runes[2])
    else:
        rune1 = int(gear.get("rune1", 0))
        rune2 = int(gear.get("rune2", 0))
        rune3 = int(gear.get("rune3", 0))

    bb.write_method_6(rune1, class_64.const_101)
    bb.write_method_6(rune2, class_64.const_101)
    bb.write_method_6(rune3, class_64.const_101)

    colors = gear.get("colors")
    if isinstance(colors, (list, tuple)) and len(colors) >= 2:
        color1, color2 = int(colors[0]), int(colors[1])
    else:
        color1 = int(gear.get("color1", 0))
        color2 = int(gear.get("color2", 0))

    bb.write_method_6(color1, class_21.const_50)
    bb.write_method_6(color2, class_21.const_50)

def build_gear_change_packet(entity_id: int, equipped_gears: list[dict]) -> bytes:
    """
    equipped gears = list of 6 gear dicts (slots 1–6)
    """
    bb = BitBuffer()
    bb.write_method_4(entity_id)

    # Slots 1..6 (skip slot 0)
    for slot in range(6):
        gear = equipped_gears[slot] if slot < len(equipped_gears) else None

        if gear and gear.get("gearID", 0) > 0:
            bb.write_method_15(True)  # slot exists
            bb.write_method_15(True)  # gear exists
            write_enttype_gear(bb, gear)
        else:
            bb.write_method_15(True)  # slot exists
            bb.write_method_15(False)  # empty slot → client builds No<Class><Slot>

    payload = bb.to_bytes()
    return struct.pack(">HH", 0xAF, len(payload)) + payload

def broadcast_gear_change(session, all_sessions):
    char = session.current_char_dict
    if not char:
        return

    entity_id = session.clientEntID
    equipped = char.get("equippedGears", [])

    pkt = build_gear_change_packet(entity_id, equipped)

    for other in all_sessions:
        if (
                other is not session
                and other.player_spawned
                and other.current_level == session.current_level
        ):
            other.conn.sendall(pkt)

def send_gear_to_self(session):
    """
    Send gear packet to the player themselves.
    This ensures the client recalculates find stats from equipped runes
    after zone transitions.
    """
    char = session.current_char_dict
    if not char:
        return
    
    entity_id = session.clientEntID
    if entity_id is None:
        return
    
    equipped = char.get("equippedGears", [])
    pkt = build_gear_change_packet(entity_id, equipped)
    session.conn.sendall(pkt)

def apply_and_broadcast_hp_delta(
    *,
    source_session,
    ent_id: int,
    delta: int,
    all_sessions,
    source_name: str,
):

    bb = BitBuffer()
    bb.write_method_4(ent_id)
    bb.write_method_45(delta)

    payload = bb.to_bytes()
    pkt = struct.pack(">HH", 0x3A, len(payload)) + payload

    for other in all_sessions:
        if other.player_spawned:
            # Skip if this is the source session (already handled separately if needed)
            if source_session and other is source_session:
                continue
            
            # Broadcast to all players in the same level
            # We use target player's level if source_session is missing
            target_level = source_session.current_level if source_session else getattr(other, "current_level", None)
            if other.current_level == target_level:
                other.conn.sendall(pkt)


        # game client function handlers
       #####################################

def handle_entity_destroy(session, data):
    br = BitReader(data[4:])
    entity_id = br.read_method_9()

    level = session.current_level
    # remove from this session
    session.entities.pop(entity_id, None)

    # If this was the client’s own entity, clear reference
    if session.clientEntID == entity_id:
        session.clientEntID = None

    level_map = GS.level_entities.get(level)
    if level_map and entity_id in level_map:
        del level_map[entity_id]
        # print(f"[DESTROY] Entity {entity_id} removed from level {level}")

    for other in GS.all_sessions:
        if (
            other is not session
            and other.player_spawned
            and other.current_level == level
        ):
            other.conn.sendall(data)

    # Tutorial Dungeon: Chains Destruction Trigger
    if session.current_level == "TutorialDungeon":
        # Chains02 (ID: 3268190) - First Room
        if entity_id == 3268190:
             print(f"[{session.addr}] [Tutorial] Chains02 (Start) destroyed. Script should start.")
             
        # Chains03 (ID: 4054622) - Boss Room
        elif entity_id == 4054622: 
            print(f"[{session.addr}] [Tutorial] Chains03 (End) destroyed. Triggering Anna Cinematic...")
            # Trigger cinematic on NPC Anna (ID: 3858014)
            from globals import build_start_skit_packet
            pkt = build_start_skit_packet(3858014, dialogue_id=2, mission_id=101)
            session.conn.sendall(pkt)
            
            # Backup: Trigger on Parrot (ID: 3333726)
            pkt2 = build_start_skit_packet(3333726, dialogue_id=2, mission_id=101)
            session.conn.sendall(pkt2)

def handle_buff_tick_dot(session, data):
    br = BitReader(data[4:])
    target_id = br.read_method_9()
    source_id = br.read_method_9()
    power_type_id = br.read_method_9()
    amount = br.read_method_24()

    # Broadcast unchanged packet to other players in same level
    for other in GS.all_sessions:
        if (
                other is not session
                and other.player_spawned
                and other.current_level == session.current_level
        ):
            other.conn.sendall(data)

def handle_respawn_broadcast(session, data):
    br = BitReader(data[4:])

    ent_id = br.read_method_9()
    heal_amount = br.read_method_24()
    used_potion = br.read_method_15()
    ent = session.entities.get(ent_id)

    if ent is None:
        return

    ent["dead"] = False
    ent["entState"] = 1

    char = next((c for c in session.char_list if c.get("name") == session.current_character), None)
    if char:
        level = char.get("level", 1)
        max_hp = get_base_hp_for_level(level)
    else:
        max_hp = heal_amount

    ent["hp"] = min(heal_amount, max_hp)
    if ent_id == session.clientEntID:
        session.authoritative_current_hp = int(ent["hp"])

    bb = BitBuffer()
    bb.write_method_4(ent_id)
    bb.write_method_45(heal_amount)
    payload = bb.to_bytes()
    pkt = struct.pack(">HH", 0x82, len(payload)) + payload

    for other in GS.all_sessions:
        if other is not session and other.player_spawned and other.current_level == session.current_level:
            other.conn.sendall(pkt)

def handle_request_respawn(session, data):
    br = BitReader(data[4:])
    use_potion = br.read_method_15()

    if use_potion:
        char = next((c for c in session.char_list
                     if c.get("name") == session.current_character), None)
        if char:
            for itm in char.get("consumables", []):
                if itm.get("consumableID") == 9 and itm.get("count", 0) > 0:
                    itm["count"] -= 1
                    save_characters(session.user_id, session.char_list)
                    send_consumable_update(session.conn, 9, itm["count"])
                    break
    else:
        char = next((c for c in session.char_list
                     if c.get("name") == session.current_character), None)

    # Compute heal amount based on level
    level = char.get("level", 1)
    heal_amount = get_base_hp_for_level(level)

    # Send RespawnComplete
    bb = BitBuffer()
    bb.write_method_24(heal_amount)
    bb.write_method_15(use_potion)
    payload = bb.to_bytes()

    session.conn.sendall(struct.pack(">HH", 0x80, len(payload)) + payload)

def handle_power_hit(session, data):
    br = BitReader(data[4:])
    target_entity_id = br.read_method_9()
    source_entity_id = br.read_method_9()
    damage_value     = br.read_method_24()
    power_type_id    = br.read_method_9()

    # Animation override
    has_animation_override = br.read_method_15()
    animation_override_id = br.read_method_9() if has_animation_override  else None

    # Hit effect override (projectile/effect index)
    has_effect_override = br.read_method_15()
    effect_override_id = br.read_method_9() if has_effect_override else None

    # Critical hit or special-flag
    is_critical = br.read_method_15()

    # --- Server-Side Drop Logic ---
    from Commands import process_drop_reward
    from game_data import calculate_npc_gold, calculate_npc_exp, get_ent_type, get_random_material_for_realm
    from game_data import calculate_npc_hp, calculate_npc_gold, get_ent_type, calculate_drop_data, get_gear_id_for_entity, get_random_gear_id
    from player_stats import calculate_find_bonuses, get_modified_gold, get_modified_drop_chance
    import random

    target = None
    level = session.current_level

    # Check session entities (players/pets/NPC props pointer)
    if target_entity_id in session.entities:
        target = session.entities[target_entity_id]
    # Check level NPCs (shared) using canonical props
    elif level:
        target = get_npc_props(level, target_entity_id)

    if not target:
        # Client-side entity (not tracked by server).
        # We MUST NOT return early, or the client won't receive the echo packet 
        # (which it might need for confirming the hit/projectile).
        # We just skip server-side HP tracking and loot logic for this entity.
        # print(f"[Combat] Target {target_entity_id} unknown - treating as client-side entity (broadcasting only).")
        pass
    
    if target:
        ent_name = target.get("name")
        ent_type_for_behavior = get_ent_type(ent_name) if ent_name else None
        behavior_name = ent_type_for_behavior.get("Behavior", "") if ent_type_for_behavior else ""
        is_treasure_chest = behavior_name == "TreasureChest" or (ent_name or "").startswith("TreasureChest")
        # Initialize HP if missing (Authoritative fallback)
        if "hp" not in target:
            # Special initialization for player from session metadata
            if target_entity_id == session.clientEntID and hasattr(session, "authoritative_max_hp"):
                max_hp = session.authoritative_max_hp
                target["hp"] = max_hp
                target["max_hp"] = max_hp
                target["level"] = session.current_char_dict.get("level", 1)
                target["rewards_granted"] = False
            else:
                ent_type_data = get_ent_type(ent_name) if ent_name else None
                if ent_type_data is None:
                    ent_type_data = {}
                npc_level = int(ent_type_data.get("Level", "1"))
                
                max_hp = calculate_npc_hp(ent_name, npc_level)
                # Treasure chests in data can resolve to 0 HP (Level 0 + tiny HitPoints scalar),
                # but they should still break on hit and always drop gold.
                if is_treasure_chest and max_hp <= 0:
                    max_hp = 1
                target["hp"] = max_hp
                target["max_hp"] = max_hp
                target["level"] = npc_level
                target["rewards_granted"] = False
        
        current_hp = target["hp"]
        # NPC can be alive again while an old rewards flag is still set (respawned without full reset).
        if current_hp > 0 and target.get("rewards_granted", False):
            target["rewards_granted"] = False
        # If a chest was spawned/loaded with 0 HP, treat the first incoming hit as lethal.
        if is_treasure_chest and current_hp <= 0 and not target.get("rewards_granted", False):
            current_hp = 1
        new_hp = current_hp - damage_value
        target["hp"] = new_hp
    else:
        # Unknown target (Client-side mob), skip server HP logic
        # Check if this damage has already been applied (prevent double damage from client-spawned enemies)
        current_time = time.monotonic()
        if target_entity_id in session.entities and session.entities[target_entity_id].get("_last_damage_time") == current_time:
            print(f"[Combat] Duplicate damage blocked for client-spawned entity {target_entity_id}")
            return
        current_hp = 100
        new_hp = 100 - damage_value
        ent_name = "Unknown"
        
        # Mark this damage as processed
        if target_entity_id not in session.entities:
            session.entities[target_entity_id] = {}
        session.entities[target_entity_id]["_last_damage_time"] = current_time

        # print(f"[Combat] Entity {target_entity_id} HP: {current_hp} -> {new_hp}")

    ent_name = target.get("name") if target else "Unknown"
    # Trigger reward ONLY on lethal damage and if not already granted
    # NOTE: target is None for client-spawned mobs — rewards for those go through
    # handle_grant_reward in Commands.py, so we skip this block entirely.
    if target and new_hp <= 0 and current_hp > 0 and not target.get("rewards_granted", False):
        # Verify it's an enemy (not player/pet/neutral)
        team = target.get("team", 0)
        # print(f"[Combat] Lethal Hit {ent_name} (Team={team})")
        if team == 2 or (not target.get("is_player", False) and team != 1 and team != 3):
            # Ensure the attacker is this player's entity/pet to avoid stray XP awards
            attacker = session.entities.get(source_entity_id)
            if not attacker:
                 # It's possible attacker is another player or external source?
                 # But we usually only process local session packets for local hits?
                 # Actually handle_power_hit comes from Client A. source_entity_id must be known to Client A.
                 pass
            
            # Allow lenient attacker check for debugging if needed, but standard logic requires it.
            if not attacker or attacker.get("team") not in (0, 1) and not attacker.get("is_player", False):
                print(f"[Combat] Lethal ignored: Attacker {source_entity_id} invalid/wrong team")
                return
            target["rewards_granted"] = True
            target["hp"] = 0
            target["death_count"] = int(target.get("death_count", 0)) + 1
            death_count = target["death_count"]

            # Track dungeon kill progress
            progress = None
            if not is_treasure_chest:
                progress = record_dungeon_kill(level, target_entity_id, user_id=session.user_id)
            if progress:
                for s in GS.all_sessions:
                    if s.player_spawned and s.current_level == level:
                        send_quest_progress(s, progress["percent"])
                        if s.current_char_dict:
                            s.current_char_dict["questTrackerState"] = progress["percent"]
            
            npc_level = target.get("level", 1)
            
            # Calculate player's find bonuses from equipped charm runes
            char = session.current_char_dict
            find_bonuses = calculate_find_bonuses(char) if char else {"gold_find": 0, "item_find": 0, "craft_find": 0}
            
            # Apply gold find bonus
            base_gold = calculate_npc_gold(ent_name, npc_level)
            # TreasureChest entities always drop big gold and are loot-only.
            if is_treasure_chest:
                player_level = char.get("level", 1) if char else 1
                base_gold = 500 + (player_level * 20) + random.randint(0, 500)
            gold_amount = get_modified_gold(base_gold, find_bonuses.get("gold_find", 0))
            xp_amount = 0 if is_treasure_chest else calculate_npc_exp(ent_name, npc_level)
            if xp_amount > XP_CAP_PER_KILL:
                print(f"[Combat] XP capped for {ent_name}: {xp_amount} -> {XP_CAP_PER_KILL}")
                xp_amount = XP_CAP_PER_KILL
            
            # Send XP reward immediately
            if xp_amount > 0:
                send_xp_reward(session, xp_amount)
            
            # Add XP to character and check for level up
            char = session.current_char_dict
            if char and xp_amount > 0:
                xp_gain = int(xp_amount)
                current_xp = int(char.get("xp", 0) or 0) + xp_gain
                char["xp"] = current_xp

                # Auto level-up: calculate level from XP
                from game_data import get_player_level_from_xp
                old_level = int(char.get("level", 1) or 1)
                new_level = get_player_level_from_xp(current_xp)
                if new_level > old_level:
                    char["level"] = new_level
                    print(f"[Combat] {char.get('name', 'Player')} LEVELED UP! {old_level} -> {new_level}")

                # --- Pet XP from combat kill ---
                active_pet_info = char.get("activePet") or {}
                pet_type_id = int(active_pet_info.get("typeID", 0) or 0)
                pet_special_id = int(active_pet_info.get("special_id", 0) or 0)

                if pet_type_id > 0:
                    pets_list = char.get("pets", [])
                    target_pet = next(
                        (p for p in pets_list
                         if int(p.get("typeID", 0) or 0) == pet_type_id
                         and int(p.get("special_id", 0) or 0) == pet_special_id),
                        None,
                    )
                    if target_pet is None and pet_special_id == 0:
                        target_pet = next(
                            (p for p in pets_list if int(p.get("typeID", 0) or 0) == pet_type_id),
                            None,
                        )

                    if target_pet:
                        pet_xp = int(target_pet.get("xp", 0) or 0) + xp_gain
                        target_pet["xp"] = pet_xp
                        current_pet_level = int(target_pet.get("level", 1) or 1)
                        active_pet_info["xp"] = pet_xp
                        active_pet_info["level"] = current_pet_level
                        send_pet_xp_update(
                            session, pet_type_id, pet_special_id,
                            xp_gain, current_pet_level, False
                        )

                print(f"[Combat] {char.get('name', 'Player')} gained {xp_gain} XP (Total: {current_xp})")
                save_characters(session.user_id, session.char_list)
            
            # Calculate HP gain for globe
            player_max_hp = getattr(session, "authoritative_max_hp", 100)
            ent_type_for_rank = get_ent_type(ent_name)
            rank = ent_type_for_rank.get("EntRank", "Minion") if ent_type_for_rank else "Minion"
            
            hp_percent = 0.4 if rank in ["Lieutenant", "Boss", "MiniBoss"] else 0.15
            hp_gain = 0 if is_treasure_chest else int(player_max_hp * hp_percent)
            
            # Get material drop based on enemy's Realm
            ent_type_data = get_ent_type(ent_name)
            realm = ent_type_data.get("Realm", "") if ent_type_data else ""
            material_id = None
            
            # Check if current level is a dungeon
            # LEVEL_CONFIG[name] = (swf, map_id, base_id, is_dungeon)
            is_dungeon = LEVEL_CONFIG.get(level, ("", 0, 0, False))[3]

            # Apply craft find bonus to material drop chance
            base_material_chance = 0.3  # 30% base chance
            material_chance = get_modified_drop_chance(base_material_chance, find_bonuses.get("craft_find", 0))
            if not is_treasure_chest and is_dungeon and realm and random.random() < material_chance:
                material_id = get_random_material_for_realm(realm)

            # Calculate drops based on difficulty tiers with item find bonus
            specific_gear_id = None
            if is_treasure_chest:
                should_drop_gear, gear_tier = False, 0
            elif is_dungeon:
                should_drop_gear, gear_tier = calculate_drop_data(ent_name, npc_level, rank, find_bonuses.get("item_find", 0))
                if should_drop_gear:
                    specific_gear_id = get_gear_id_for_entity(ent_name)
                    if not specific_gear_id:
                        # Fall back to class-specific random gear
                        player_class = (char.get("class") or "").title() if char else None
                        specific_gear_id = get_random_gear_id(player_class)
                    if not specific_gear_id:
                        should_drop_gear = False
            else:
                should_drop_gear, gear_tier = False, 0

            # Spawn loot drops for both dungeon and non-dungeon kills
            death_x = int(round(target.get("pos_x", target.get("x", 0))))
            death_y = int(round(target.get("pos_y", target.get("y", 0))))
            process_drop_reward(
                session,
                death_x,
                death_y,
                gold=gold_amount,
                hp_gain=hp_gain,
                drop_gear=should_drop_gear,
                gear_tier=gear_tier,
                material_id=material_id,
                target_id=target_entity_id,
                specific_gear_id=specific_gear_id,
                reward_nonce=death_count,
            )
            print(f"[Combat] Lethal on {ent_name} ({rank}, Realm={realm}). Dropping {gold_amount} Gold, {hp_gain} HP, XP={xp_amount}, Material={material_id}.")

            # Tutorial Dungeon Special Logic: Destroy Chains immediately on death
            if session.current_level == "TutorialDungeon" and target_entity_id in [3268190, 4054622]:
                print(f"[Combat] Tutorial Chains {target_entity_id} destroyed! Forcing server-side removal.")
                # Force instant destruction so client sees them vanish/defeated
                # This triggers handle_entity_destroy -> triggers StartSkit (for Chains03)
                handle_entity_destroy_server(session, target_entity_id, GS.all_sessions)

    # If the target is a player, send an authoritative HP update (0x3A).
    # Some client flows ignore HP loss in the raw 0x0A hit packet for self.
    target_player_session = None
    if target and target.get("is_player", False):
        # Find the session for this player entity
        if target.get("id") == session.clientEntID:
            target_player_session = session
        else:
            for s in GS.all_sessions:
                if s.clientEntID == target.get("id"):
                    target_player_session = s
                    break
    
    if target_player_session:
         new_hp_int = max(0, int(new_hp))
         max_hp_for_target = getattr(target_player_session, "authoritative_max_hp", None)
         if max_hp_for_target is not None:
             new_hp_int = min(new_hp_int, int(max_hp_for_target))
         target_player_session.authoritative_current_hp = new_hp_int

         target_ent = target_player_session.entities.get(target.get("id")) if target else None
         if target_ent is not None:
             target_ent["hp"] = new_hp_int
             if target.get("max_hp") is not None:
                 target_ent["max_hp"] = target.get("max_hp")

         # Send actual HP loss (negative delta)
         # Note: damage_value is positive, so we send -damage_value
         # send_hp_update(target_player_session, target.get("id"), -damage_value)

    # Forward packet unchanged to other clients in same level
    # We MUST NOT echo it back to the sender (session) even if they are the target,
    # because they already processed the hit locally. Echoing causes double damage visuals.
    for other in GS.all_sessions:
        if (
                other is not session
                and other.player_spawned
                and other.current_level == session.current_level
        ):
            other.conn.sendall(data)

def handle_projectile_explode(session, data):
    br = BitReader(data[4:])
    entity_id      = br.read_method_9()
    remote_missile = br.read_method_9()
    coordinate_x   = br.read_method_24()
    coordinate_y   = br.read_method_24()
    is_crit        = br.read_method_15()

    # Broadcast unchanged packet to all other players in same level (No Echo)
    for other in GS.all_sessions:
        if (
            other is not session
            and other.player_spawned
            and other.current_level == session.current_level
        ):
            other.conn.sendall(data)
# TODO:
#   Buffs are currently not stored or simulated server-side.
#   The client fully handles buff logic, but it STILL depends on the
#   server to send buff removal events.
#
#   For server-spawned entities :
#       - Without server-side buff tracking,
#         buffs applied by players become permanent.
#       - The server must eventually track:
#           • buff start time
#           • buff duration
#           • stack count
#           • modifier nodes (powerNodeTypeID + modValues)
#           • unique sequence IDs
#
#   In the future, server must store these values to correctly
#   handle timed buff removal and expiration logic.
def handle_add_buff(session, data):
    br = BitReader(data[4:])
    entity_id    = br.read_method_9()
    caster_id    = br.read_method_9()
    buff_type_id = br.read_method_9()
    duration     = br.read_method_9()
    stack_count  = br.read_method_9()
    sequence_id  = br.read_method_9()
    has_modifier_nodes = br.read_method_15()

    if has_modifier_nodes:
        node_count = br.read_method_9()

        for _ in range(node_count):
            power_node_type_id = br.read_method_9()
            mod_value_count    = br.read_method_9()

            mod_values = []
            for _ in range(mod_value_count):
                mod_value = br.read_method_560()
                mod_values.append(mod_value)

    # Track buff server-side for NPCs (team 2 only)
    target_props = get_npc_props(session.current_level, entity_id)
    if target_props and target_props.get("team") == 2:
        buffs = target_props.setdefault("buffs", [])
        expires_at = time.time() + duration
        updated = False
        for buff in buffs:
            if buff.get("instance_id") == sequence_id:
                buff.update({
                    "buff_type_id": buff_type_id,
                    "stack_count": stack_count,
                    "expires_at": expires_at,
                    "duration": duration,
                    "caster_id": caster_id,
                })
                updated = True
                break
        if not updated:
            buffs.append({
                "buff_type_id": buff_type_id,
                "instance_id": sequence_id,
                "stack_count": stack_count,
                "expires_at": expires_at,
                "duration": duration,
                "caster_id": caster_id,
            })

    # Broadcast unchanged packet to other clients in same level
    for other in GS.all_sessions:
        if (
            other is not session
            and other.player_spawned
            and other.current_level == session.current_level
        ):
            other.conn.sendall(data)

"""
TODO:
    The server does NOT currently track buff timers or stacks.
    For server-spawned entities, buffs never expire unless the
    server sends this packet. In the future, the server must
    store:
        • buff_type_id
        • instance_id
        • duration
        • stack count
        • start time
    so it can send timed buff removals correctly.
"""
def handle_remove_buff(session, data):
    br = BitReader(data[4:])
    entity_id      = br.read_method_9()
    buff_type_id   = br.read_method_9()
    instance_id    = br.read_method_9()

    # Broadcast packet unchanged to other players in the same level
    for other in GS.all_sessions:
        if (
            other is not session
            and other.player_spawned
            and other.current_level == session.current_level
        ):
            other.conn.sendall(data)

def handle_change_max_speed(session, data):
    br = BitReader(data[4:])
    entity_id     = br.read_method_9()
    speed_mod_int = br.read_method_9()
    for other in GS.all_sessions:
        if (
            other.player_spawned
            and other.current_level == session.current_level
        ):
            other.conn.sendall(data)


def handle_power_cast(session, data):
    br = BitReader(data[4:])

    ent_id   = br.read_method_9()
    power_id = br.read_method_9()

    # Skip has-target-entity flag (unused by client)
    has_target_entity = br.read_method_15()

    # Target position if ranged/projectile attacks
    has_target_pos = br.read_method_15()
    if has_target_pos:
        target_x = br.read_method_24()
        target_y = br.read_method_24()

    has_projectile = br.read_method_15()
    if has_projectile:
        projectile_id = br.read_method_9()

    # Charged variant
    is_charged = br.read_method_15()

    # Combo / alternate variant
    has_extra = br.read_method_15()
    if has_extra:
        is_secondary = br.read_method_15()
        if is_secondary:
            secondary_id = br.read_method_9()
        else:
            tertiary_id = br.read_method_9()

    # Cooldown & mana flags
    has_flags = br.read_method_15()
    if has_flags:
        has_cooldown_tick = br.read_method_15()
        if has_cooldown_tick:
            cooldown_tick = br.read_method_9()

        has_mana_cost = br.read_method_15()
        if has_mana_cost:
            MANA_BITS = PowerType.const_423
            mana_cost = br.read_method_6(MANA_BITS)

    # Broadcast unchanged packet
    for other in GS.all_sessions:
        if (
            other is not session
            and other.player_spawned
            and other.current_level == session.current_level
        ):
            other.conn.sendall(data)

def handle_change_offset_y(session, data):
    br = BitReader(data[4:])
    entity_id = br.read_method_9()
    offset_y  = br.read_method_739()

    pkt = build_change_offset_y_packet(entity_id, offset_y)

    for s in GS.all_sessions:
        if s is not session and s.player_spawned and s.current_level == session.current_level:
            try:
                s.conn.sendall(pkt)
            except:
                pass


# Sent when equipment, runes, or stats change and HP
def handle_char_regen(session, data):
    br = BitReader(data[4:])
    ent_id = br.read_method_9()
    delta  = br.read_method_24()

    apply_and_broadcast_hp_delta(
        source_session=session,
        ent_id=ent_id,
        delta=delta,
        all_sessions=GS.all_sessions,
        source_name="GEAR/STAT",
    )


# Sent periodically by the client when passive regeneration occurs.
def handle_char_regen_tick(session, data):
    br = BitReader(data[4:])
    ent_id = br.read_method_9()
    delta  = br.read_method_24()

    apply_and_broadcast_hp_delta(
        source_session=session,
        ent_id=ent_id,
        delta=delta,
        all_sessions=GS.all_sessions,
        source_name="REGEN",
    )


def handle_equip_rune(session,  data):
    br = BitReader(data[4:])

    entity_id = br.read_method_4()
    gear_id   = br.read_method_6(GearType.GEARTYPE_BITSTOSEND)
    gear_tier = br.read_method_6(GearType.const_176)
    rune_id   = br.read_method_6(class_64.const_101)
    rune_slot = br.read_method_6(class_1.const_765)  # 1–3

    # Validate rune slot
    if rune_slot not in (1, 2, 3):
        print(f" Warning : Invalid rune slot: {rune_slot}")
        return

    rune_idx = rune_slot - 1

    char = next(
        (c for c in session.char_list if c.get("name") == session.current_character),
        None
    )

    equipped = char.setdefault("equippedGears", [])
    inventory = char.setdefault("inventoryGears", [])
    charms = char.setdefault("charms", [])

    # Normalize equipped gear slots
    required_slots = EntType.MAX_SLOTS - 1
    while len(equipped) < required_slots:
        equipped.append({
            "gearID": 0,
            "tier": 0,
            "runes": [0, 0, 0],
            "colors": [0, 0],
        })
    if len(equipped) > required_slots:
        equipped[:] = equipped[:required_slots]

    # Locate all instances of the target gear (equipped and inventory)
    matching_gears = [
        g for g in equipped if g.get("gearID") == gear_id and g.get("tier") == gear_tier
    ] + [
        g for g in inventory if g.get("gearID") == gear_id and g.get("tier") == gear_tier
    ]

    if not matching_gears:
        print(f" Warning : Targeted gear {gear_id} (Tier {gear_tier}) not found in equipped or inventory")
        return

    # Use the first match to determine old rune state
    gear = matching_gears[0]
    old_rune = gear["runes"][rune_idx]

    def resolve_charm_entry_id(entry):
        if not isinstance(entry, dict):
            return None

        c_id = entry.get("charmID")
        if c_id is None:
            c_id = entry.get("id")

        if c_id is None and entry.get("charmName"):
            try:
                from constants import get_charm_id
                c_id = get_charm_id(entry.get("charmName"))
                if c_id:
                    entry["charmID"] = c_id
            except Exception:
                c_id = None

        try:
            return int(c_id) if c_id is not None else None
        except (TypeError, ValueError):
            return None

    def add_charm(charm_id, amount=1):
        for c in charms:
            c_id = resolve_charm_entry_id(c)
            if c_id == charm_id:
                c["count"] = int(c.get("count", 0)) + amount
                return
        charms.append({"charmID": charm_id, "count": amount})

    def consume_charm(charm_id):
        for c in charms:
            c_id = resolve_charm_entry_id(c)
            if c_id == charm_id:
                if "count" in c:
                    c["count"] = int(c.get("count", 0)) - 1
                    if c["count"] <= 0:
                        charms.remove(c)
                else:
                    # If count is missing, assume 1 and remove
                    charms.remove(c)
                return True
        return False

    # Rune removal (ID 96)
    if rune_id == 96:
        for g_item in matching_gears:
            g_item["runes"][rune_idx] = 0

        if old_rune and old_rune != 96:
            add_charm(old_rune)

        if not consume_charm(96):
            print(" Warning : Rune remover (96) missing from charms")

    # Equip / Replace rune
    else:
        # Consume the new rune (always)
        if not consume_charm(rune_id):
            print(f" Warning : Rune {rune_id} missing from charms")
            return

        # Equip rune in all matched instances
        for g_item in matching_gears:
            g_item["runes"][rune_idx] = rune_id
            
        print(f"[DEBUG] Socketed Rune {rune_id} into slot {rune_idx} for all instances of gear {gear_id}. New Runes: {gear['runes']}")

    save_characters(session.user_id, session.char_list)

    bb = BitBuffer()
    bb.write_method_4(entity_id)
    bb.write_method_6(gear_id, GearType.GEARTYPE_BITSTOSEND)
    bb.write_method_6(gear_tier, GearType.const_176)
    bb.write_method_6(rune_id, class_64.const_101)
    bb.write_method_6(rune_slot, class_1.const_765)

    payload = bb.to_bytes()
    packet = struct.pack(">HH", 0xB0, len(payload)) + payload
    session.conn.sendall(packet)

def handle_update_single_gear(session, data):
    br = BitReader(data[4:])

    entity_id = br.read_method_4()
    slot_raw  = br.read_method_236()        # 1-based
    gear_id   = br.read_method_6(GearType.GEARTYPE_BITSTOSEND)

    slot = slot_raw - 1  # convert to 0-based

    # Locate active character
    char = next(
        (c for c in session.char_list if c.get("name") == session.current_character),
        None
    )

    inv = char.setdefault("inventoryGears", [])
    eq  = char.setdefault("equippedGears", [])

    # Normalize equipped slots (6)
    while len(eq) < 6:
        eq.append({
            "gearID": 0,
            "tier": 0,
            "runes": [0, 0, 0],
            "colors": [0, 0],
        })

    # Find gear in inventory OR equipped (to prevent rune wipe if already equipped)
    gear_data = next(
        (g for g in inv if g.get("gearID") == gear_id),
        next((g for g in eq if g.get("gearID") == gear_id), None)
    )

    if gear_data:
        gear_data = gear_data.copy()
    else:
        gear_data = {
            "gearID": gear_id,
            "tier": 0,
            "runes": [0, 0, 0],
            "colors": [0, 0],
        }
        inv.append(gear_data.copy())

    # Apply to equipped slot
    eq[slot] = gear_data

    save_characters(session.user_id, session.char_list)
    broadcast_gear_change(session, GS.all_sessions)


def handle_update_equipment(session, data):
    br = BitReader(data[4:])
    entity_id = br.read_method_9()

    char = session.current_char_dict
    equipped = char.setdefault("equippedGears", [])
    inventory = char.setdefault("inventoryGears", [])
    SLOT_COUNT = EntType.MAX_SLOTS - 1

    def empty_gear():
        return {
            "gearID": 0,
            "tier": 0,
            "runes": [0, 0, 0],
            "colors": [0, 0],
        }

    while len(equipped) < SLOT_COUNT:
        equipped.append(empty_gear())

    for slot in range(SLOT_COUNT):
        changed = br.read_method_15()

        if not changed:
            continue

        gear_id = br.read_method_20(GearType.GEARTYPE_BITSTOSEND)

        item = next(
            (g for g in inventory if g.get("gearID") == gear_id),
            next((g for g in equipped if g.get("gearID") == gear_id), None)
        )

        equipped[slot] = item.copy() if item else {
            "gearID": gear_id,
            "tier": 0,
            "runes": [0, 0, 0],
            "colors": [0, 0],
        }

    save_characters(session.user_id, session.char_list)
    broadcast_gear_change(session, GS.all_sessions)


def handle_create_gearset(session, data):
    br = BitReader(data[4:])
    slot_idx = br.read_method_20(GearType.const_348)

    char = next(
        (c for c in session.char_list
         if c.get("name") == session.current_character),
        None
    )
    gearsets = char.setdefault("gearSets", [])

    while len(gearsets) <= slot_idx:
        if len(gearsets) >= Game.const_1057:
            return

        gearsets.append({
            "name": f"GearSet {len(gearsets) + 1}",
            "slots": [0] * EntType.MAX_SLOTS
        })

    save_characters(session.user_id, session.char_list)


def handle_name_gearset(session, data):
    br = BitReader(data[4:])
    slot_idx = br.read_method_20(GearType.const_348)
    name = br.read_method_26()

    char = next(
        (c for c in session.char_list
         if c.get("name") == session.current_character),
        None
    )

    gearsets = char.get("gearSets", [])
    if slot_idx >= len(gearsets):
        print("ERROR: gearset does not exist")
        return

    gearsets[slot_idx]["name"] = name

    save_characters(session.user_id, session.char_list)


def handle_update_gearset(session, data):
    br = BitReader(data[4:])
    gearset_index = br.read_method_20(GearType.const_348)
    char = session.current_char_dict

    gearsets = char.setdefault("gearSets", [])
    if gearset_index >= len(gearsets):
        print("[0xC6] Invalid gearset index", gearset_index)
        return

    equipped = char.get("equippedGears", [])

    gs = gearsets[gearset_index]
    slots = gs.setdefault("slots", [0] * 7)

    if len(slots) < 7:
        slots.extend([0] * (7 - len(slots)))
    elif len(slots) > 7:
        del slots[7:]

    for i in range(6):
        gear_id = int(equipped[i].get("gearID", 0)) if i < len(equipped) else 0
        slots[i + 1] = gear_id

    save_characters(session.user_id, session.char_list)
