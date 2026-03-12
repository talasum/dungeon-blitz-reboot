import json
import os
import re
import struct
import threading
import time

from typing import Dict, Any
from BitBuffer import BitBuffer
from bitreader import BitReader
from constants import Entity, class_7, class_20, class_3, Game, LinkUpdater, EntType, GearType, class_64, class_21, class_118, method_277
from globals import GS, init_dungeon_run


def _refresh_crafttown_buildings_on_spawn(session):
    from WorldEnter import send_building_update

    def _send_once(delay_sec: float):
        def _worker():
            if delay_sec > 0:
                time.sleep(delay_sec)
            if not getattr(session, "running", False):
                return
            if getattr(session, "current_level", None) != "CraftTown":
                return
            latest_char = getattr(session, "current_char_dict", None) or {}
            send_building_update(session, latest_char)

        threading.Thread(target=_worker, daemon=True).start()

    # Keep a short retry window to cover delayed UI/asset readiness.
    for delay in (0.0, 1.2, 2.8):
        _send_once(delay)

def _norm_identity_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())

def _request_client_combat_stats_sync(session):
    if not session or not getattr(session, "conn", None):
        return
    bb = BitBuffer()
    bb.write_method_6(0, Game.const_794)
    bb.write_method_4(0)
    payload = bb.to_bytes()
    packet = struct.pack(">HH", 0xFB, len(payload)) + payload
    try:
        session.conn.sendall(packet)
    except OSError:
        return

"""
Hints NPCs data 
[
    {
      "id": 3,
      "name": "NPCRuggedVillager02",
      "x": 3317,
      "y": 461,
      "v": 0,
      "team": 3,
      "untargetable": false,
      "render_depth_offset": -15,
      "behavior_speed": 0.0,
      "character_name": "NR_Mayor01", 
      "DramaAnim": "",
      "SleepAnim": "",
      "summonerId": 0,
      "power_id": 0,
      "entState": 0,
      "facing_left": true,
      "health_delta": 0,
      "buffs": []
    }
]

======== Intercatible NPCs Tips =====================
- how to make the NPC interactable by the player
- NPC will only become interactable if they have a "character_name" set and  "team" set to 3 

- look at the "MissionTypes.Json" for these 2 lines on each mission : 

"ContactName": "CaptainFink",
"ReturnName": "NR_Mayor01", 

For example the NPC with the "character_name": "NR_Mayor01",  will be linked to all the missions that have "ReturnName": "NR_Mayor01",  OR "ContactName": "NR_Mayor01",

- this will also show the NPCs name under his feet "NR_Mayor01" is "Mayor Ristas"

===============

Team Types : 

 const_531:uint = 0; # team type will be automatically chosen  its  used for a entity called "EmberBush" :/ but it will also give any other NPC team 2 (enemies)
      
 GOODGUY:uint = 1; #  players 
      
 BADGUY:uint = 2; # Enemies 
      
 NEUTRAL:uint = 3; # Friendly NPC
 
entState : 
 
 0 = Active State
 
 1 = Sleep State
 
 2 = Drama State (used during cutscenes most likely) this will put the entity to sleep also make them untargetable 
 
 3 = Entity Dies when the game loads 
 
 =============== how to use "DramaAnim" and "SleepAnim" ===============
 
 for "DramaAnim" to activate you have to set the "entState" to 2  
 
 for "SleepAnim" to activate you have to set the "entState" to 1 
 
 you can find which entity uses "DramaAnim" and "SleepAnim" at EntTypes.json some entities have "DramaAnim" or "SleepAnim" defined 
 
 Example : 
      
     # goblin will spawn in the boarding ship animation 
     {
      "name": "IntroGoblinJumper",
      "DramaAnim": "board",
      "SleepAnim": "",
      "entState": 2,
    }
    
    # the eye will spawn closed 
    {
      "name": "NephitCrownEye",
      "DramaAnim": "Sleep",
      "SleepAnim": "",
      "entState": 1,
    }
"""
def load_npc_data_for_level(level_name: str) -> list:
    json_path = os.path.join("world_npcs", f"{level_name}.json")
    try:
        with open(json_path, 'r') as file:
            data = json.load(file)

        # Filter out hostile enemies (team 2) globally.
        # This removes all server-spawned enemies, forcing the client to use its own cue spawns.
        data = [npc for npc in data if npc.get("team") != 2]

        # TutorialBoat already bakes Captain Fink and Pecky into the SWF.
        # Server-spawning them creates visible duplicates.
        if level_name == "TutorialBoat":
            baked_npcs = {"IntroParrot", "NPCCaptainSteering"}
            data = [npc for npc in data if npc.get("name") not in baked_npcs]

        # TutorialDungeon carries its own parrot and password goblin cues inside
        # the room scripts. Keep Anna server-side, but do not double-spawn these.
        if level_name == "TutorialDungeon":
            baked_npcs = {"IntroParrot", "IntroGoblinNPC"}
            data = [npc for npc in data if npc.get("name") not in baked_npcs]

        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading NPC data for {level_name}: {e}")
        return []

def Send_Entity_Data(entity: Dict[str, Any]) -> bytes:
    bb = BitBuffer(debug=True)
    bb.write_method_4(entity['id'])
    bb.write_method_13(entity['name'])
    
    # Log entity being sent
    has_no_jump = entity.get("noJumpAttack", False)
    ent_name = entity.get('name', 'Unknown')
    if has_no_jump:
        print(f"[Entity Send] {ent_name} (ID: {entity['id']}) with noJumpAttack=True")
    
    if entity.get("is_player", False):
        bb.write_method_6(1, 1)
        bb.write_method_13(entity.get("class", ""))
        bb.write_method_13(entity.get("gender", ""))
        bb.write_method_13(entity.get("headSet", ""))
        bb.write_method_13(entity.get("hairSet", ""))
        bb.write_method_13(entity.get("mouthSet", ""))
        bb.write_method_13(entity.get("faceSet", ""))
        bb.write_method_6(entity.get("hairColor", 0), 24)
        bb.write_method_6(entity.get("skinColor", 0), 24)
        bb.write_method_6(entity.get("shirtColor", 0), 24)
        bb.write_method_6(entity.get("pantColor", 0), 24)
        equipped = entity.get('equippedGears', [])
        for slot in range(1, EntType.MAX_SLOTS):
            idx = slot - 1
            if idx < len(equipped) and equipped[idx] is not None:
                gear = equipped[idx]
                bb.write_method_6(1, 1)
                bb.write_method_6(gear['gearID'], GearType.GEARTYPE_BITSTOSEND)
                bb.write_method_6(gear['tier'], GearType.const_176)
                runes = gear.get('runes', [0, 0, 0])
                bb.write_method_6(runes[0], class_64.const_101)
                bb.write_method_6(runes[1], class_64.const_101)
                bb.write_method_6(runes[2], class_64.const_101)
                colors = gear.get('colors', [0, 0])
                bb.write_method_6(colors[0], class_21.const_50)
                bb.write_method_6(colors[1], class_21.const_50)
            else:
                bb.write_method_6(0, 1)
    else:
        bb.write_method_6(0, 1)

    bb.write_method_45(int(entity['x']))  # x
    bb.write_method_45(int(entity['y']))  # y
    bb.write_method_45(int(entity.get('v', 0)))  # Velocity

    bb.write_method_6(entity.get('team', 0), Entity.TEAM_BITS)

    # ── Player OR NPC branch ──
    if entity.get("is_player", False):
        bb.write_method_6(1, 1)

        timing_flag = entity.get("idle_reset", False)
        bb.write_method_6(1 if timing_flag else 0, 1)

        appearance_flag = entity.get("spawn_fx", False)  # True for new player  spawns if the player is already in the level then it is False
        bb.write_method_6(1 if appearance_flag else 0, 1)

        active_pet = entity.get("activePet", {})
        bb.write_method_6(active_pet.get("petID",      0), class_7.const_19)
        bb.write_method_6(active_pet.get("special_id", 0), class_7.const_75)
        bb.write_method_6(entity.get("equippedMount",  0), class_20.const_297)
        bb.write_method_6(entity.get("activeConsumableID",        0), class_3.const_69)

        abilities = entity.get("abilities", [])
        has_abilities = len(abilities) > 0
        bb.write_method_6(1 if has_abilities else 0, 1)
        if bb.debug:
            bb.debug_log.append(f"has_abilities={has_abilities}")
        if has_abilities:
            for i in range(3):
                ability = abilities[i] if i < len(abilities) and abilities[i] is not None else {"abilityID": 0, "rank": 0}
                bb.write_method_6(ability.get("abilityID", 0), class_7.const_19)
                bb.write_method_6(ability.get("rank", 0), class_7.const_75)
                if bb.debug:
                    bb.debug_log.append(
                        f"ability_{i + 1}_abilityID={ability.get('abilityID', 0)}, rank={ability.get('rank', 0)}")
    else:
        bb.write_method_6(0, 1)
        bb.write_method_6(1 if entity.get("untargetable", False) else 0, 1)
        bb.write_method_739(entity.get("render_depth_offset", 0))

        # used to set the current entity's moving speed if he has any
        speed = entity.get("behavior_speed", 0)
        if speed > 0:
            bb.write_method_6(1, 1)
            bb.write_method_4(int(speed * LinkUpdater.VELOCITY_INFLATE))
        else:
            bb.write_method_6(0, 1)

    cue = entity.get("cue_data", {})
    for key in ("character_name", "DramaAnim", "SleepAnim"):
        val = cue.get(key, "")
        bb.write_method_6(1 if val else 0, 1)
        if val:
            bb.write_method_13(val)

    summoner_id = entity.get("summonerId", 0)
    if summoner_id:
        bb.write_method_6(1, 1)
        bb.write_method_4(summoner_id)
        if bb.debug:
            bb.debug_log.append(f"summonerId = {summoner_id}")
    else:
        bb.write_method_6(0, 1)

    power_id = entity.get("power_id", 0)

    if power_id > 0:
        bb.write_method_6(1, 1)
        bb.write_method_4(power_id)
        if bb.debug:
            bb.debug_log.append(f"powerTypeID = {power_id}")
    else:
        bb.write_method_6(0, 1)

    bb.write_method_6(entity.get("entState", 0), Entity.const_316)
    bb.write_method_6(1 if entity.get("facing_left", False) else 0, 1)
    
    # Send noJumpAttack flag for monsters to prevent jumping during attacks
    bb.write_method_6(1 if entity.get("noJumpAttack", False) else 0, 1)
    
    if entity.get('is_player', False):

        level = entity.get("level", 0)
        bb.write_method_6(level, Entity.MAX_CHAR_LEVEL_BITS)
        if bb.debug:
            bb.debug_log.append(f"level={level}")

        class_id = entity.get("MasterClass", Game.const_526)
        bb.write_method_6(class_id, Game.const_209)

        # Talent data is ONLY allowed if a MasterClass has been equipped
        has_talent_tree = (
                class_id != Game.const_526 and
                any(
                    t and t.get("nodeID", 0) > 0 and t.get("points", 0) > 0
                    for t in entity.get("talents", [])
                )
        )

        bb.write_method_6(1 if has_talent_tree else 0, 1)

        if has_talent_tree:
            for slot in range(class_118.NUM_TALENT_SLOTS):  # ALWAYS 27
                t = entity["talents"][slot] if slot < len(entity["talents"]) else None

                if t and t.get("nodeID", 0) > 0 and t.get("points", 0) > 0:
                    bb.write_method_6(1, 1)
                    bb.write_method_6(t["nodeID"], class_118.const_127)
                    bb.write_method_6(t["points"] - 1, method_277(slot))
                else:
                    bb.write_method_6(0, 1)


    else:
        bb.write_method_6(0, 1)

    # updates the entity's Health if that specific entity has lost any amount of health
    value = int(round(entity.get("health_delta", 0)))
    bb.write_method_45(value)

    # Updates the entities buffs if he has any
    buffs = entity.get("buffs", [])
    bb.write_method_4(len(buffs))
    for buff in buffs:
        bb.write_method_4(buff.get("type_id", 0))
        bb.write_method_4(buff.get("param1", 0))
        bb.write_method_4(buff.get("param2", 0))
        bb.write_method_4(buff.get("param3", 0))
        bb.write_method_4(buff.get("param4", 0))
        extra = buff.get("extra_data", [])
        bb.write_method_6(1 if extra else 0, 1)
        if extra:
            bb.write_method_4(len(extra))
            for ed in extra:
                bb.write_method_4(ed.get("id", 0))
                vals = ed.get("values", [])
                bb.write_method_4(len(vals))
                for v in vals:
                    bb.write_float(v)
    return bb.to_bytes()

def build_entity_dict(eid, char, props):
    """
    Build a dictionary for Send_Entity_Data packet.
    Works for both joiner (new spawn) and existing entities.
    """
    ent_dict = {
        "id": eid,
        "name": char.get("name", props.get("ent_name", "")) if char else props.get("ent_name", ""),
        "is_player": True if char else bool(props.get("is_player", False)),
        "x": int(props.get("pos_x", 0)),
        "y": int(props.get("pos_y", 0)),
        "v": int(props.get("velocity_x", 0)),
        "team": int(props.get("team", 1)),
        "buffs": list(props.get("buffs", [])),
        "facing_left": bool(props.get("b_left", False)),
    }
    if char:
        ent_dict.update({
            "class": char.get("class", ""),
            "gender": char.get("gender", ""),
            "headSet": char.get("headSet", ""),
            "hairSet": char.get("hairSet", ""),
            "mouthSet": char.get("mouthSet", ""),
            "faceSet": char.get("faceSet", ""),
            "hairColor": char.get("hairColor", 0),
            "skinColor": char.get("skinColor", 0),
            "shirtColor": char.get("shirtColor", 0),
            "pantColor": char.get("pantColor", 0),
            "equippedGears": char.get("equippedGears", []),
            "abilities": char.get("learnedAbilities", []),
            "level": char.get("level", 1),
            "MasterClass": char.get("MasterClass", 0),
            "talents": build_talent_slots(char),
            "equippedMount": char.get("equippedMount", 0)
        })

    return ent_dict

def build_talent_slots(char: dict) -> list:
    slots = [None] * class_118.NUM_TALENT_SLOTS

    master_class = char.get("MasterClass", 0)
    if master_class == 0:
        return slots

    tree = char.get("TalentTree", {})
    class_tree = tree.get(str(master_class))
    if not class_tree:
        return slots

    for node in class_tree.get("nodes", []):
        if not node.get("filled"):
            continue

        node_id = node.get("nodeID", 0)
        points  = node.get("points", 0)
        if node_id <= 0 or points <= 0:
            continue

        slot = node_id - 1
        if slot < 0 or slot >= class_118.NUM_TALENT_SLOTS:
            continue

        slots[slot] = {
            "nodeID": node_id,
            "points": points
        }

    return slots

def send_existing_entities_to_joiner(joiner):
    """
    Send spawn packets (Send_Entity_Data) ONLY for players in the same level
    to the joining player.
    NPCs are skipped and should be spawned separately by the level loader.
    """
    for other in GS.all_sessions:
        if other is joiner:
            continue
        if (
            getattr(other, "user_id", None) == getattr(joiner, "user_id", None)
            and getattr(other, "current_character", None) == getattr(joiner, "current_character", None)
        ):
            continue
        if not other.player_spawned or other.current_level != joiner.current_level:
            continue

        # Only send the entity that belongs to the player's character
        if other.clientEntID and other.clientEntID in other.entities:
            eprops = other.entities[other.clientEntID]

            char = next((c for c in other.char_list if c.get("name") == other.current_character), None)
            ent_dict = build_entity_dict(other.clientEntID, char, eprops)

            try:
                pkt = Send_Entity_Data(ent_dict)
                framed = struct.pack(">HH", 0x0F, len(pkt)) + pkt
                joiner.conn.sendall(framed)
                #print(f"[JOIN] Sent player {ent_dict['name']} (eid={other.clientEntID}) → {joiner.addr}")
            except Exception as ex:
                print(f"[JOIN] Error sending player {ent_dict['name']} to {joiner.addr}: {ex}")

def handle_entity_full_update(session, data):
    """
    Handle a full entity spawn/update (packet type 0x08)
    - Parses and stores entity info.
    - Marks player entity IDs.
    - Sends 0x0F spawn packets so players see each other.
    - Broadcasts raw 0x08 packets for movement/state sync.
    - sends 0x0F for newly-seen non-player entities (pets/minions).
    """
    br = BitReader(data[4:])

    entity_id = br.read_method_9()
    if session.current_level == "BridgeTown":
        print(f"[{session.addr}] [PKT08] Entity update from client, ID={entity_id} (len={len(data)})")
    pos_x = br.read_method_24()
    pos_y = br.read_method_24()
    velocity_x = br.read_method_24()
    ent_name = br.read_method_26()

    team = br.read_method_20(Entity.TEAM_BITS)
    is_player = bool(br.read_method_15())
    y_offset = br.read_method_706()

    # Optional cue data
    has_cue = bool(br.read_method_15())
    cue_data = {}
    if has_cue:
        if bool(br.read_method_15()):
            cname = br.read_method_13()
            cue_data["character_name"] = cname
            # DB specific: if character_name starts with a comma, it overrides the entity type
            if cname.startswith(","):
                override_name = cname[1:]
                if override_name:
                    ent_name = override_name
        if bool(br.read_method_15()):
            cue_data["DramaAnim"] = br.read_method_13()
        if bool(br.read_method_15()):
            cue_data["SleepAnim"] = br.read_method_13()

    has_summoner = bool(br.read_method_15())
    summoner_id = br.read_method_9() if has_summoner else None

    has_power = bool(br.read_method_15())
    power_id = br.read_method_9() if has_power else None

    ent_state = br.read_method_20(Entity.const_316)
    b_left = bool(br.read_method_15())
    b_running = bool(br.read_method_15())
    b_jumping = bool(br.read_method_15())
    b_dropping = bool(br.read_method_15())
    b_backpedal = bool(br.read_method_15())

    # Track client's actual in-world entity ID (not transfer token).
    # Normalize names to survive case/format differences after transitions.
    ent_name_norm = _norm_identity_name(ent_name)
    current_name_norm = _norm_identity_name(getattr(session, "current_character", None))
    is_self_packet = bool(is_player and current_name_norm and ent_name_norm == current_name_norm)

    should_update_client_eid = False
    if is_player:
        if session.clientEntID is None:
            should_update_client_eid = is_self_packet or not current_name_norm
        elif is_self_packet and session.clientEntID != entity_id:
            should_update_client_eid = True

    if should_update_client_eid and session.clientEntID != entity_id:
        old_client_ent_id = session.clientEntID
        session.clientEntID = entity_id
        if old_client_ent_id is None:
            print(f"[{session.addr}] [PKT08] Learned clientEntID = {entity_id}")
        else:
            print(
                f"[{session.addr}] [PKT08] Updated stale clientEntID: "
                f"{old_client_ent_id} -> {entity_id}"
            )

        if getattr(session, "current_level", None):
            lvl_cache = getattr(session, "_story_player_idx_by_level", None)
            if not isinstance(lvl_cache, dict):
                lvl_cache = {}
                session._story_player_idx_by_level = lvl_cache
            lvl_cache[str(session.current_level).strip().lower()] = (entity_id >> 16)

        if session.current_level == "CraftTown" and getattr(session, "crafttown_building_refresh_pending", False):
            _refresh_crafttown_buildings_on_spawn(session)
            session.crafttown_building_refresh_pending = False
    # Track client's actual in-world entity ID (not transfer token)
    if is_player and (ent_name == session.current_character or session.clientEntID is None):
        if session.clientEntID != entity_id:
            session.clientEntID = entity_id

            level = int((session.current_char_dict or {}).get("level", 1) or 1)
            level = max(1, min(level, len(Entity.PLAYER_HITPOINTS) - 1))
            fallback_max_hp = int(Entity.PLAYER_HITPOINTS[level])

            current_max_hp = int(getattr(session, "authoritative_max_hp", 0) or 0)
            if current_max_hp <= 0 or current_max_hp <= 100:
                session.authoritative_max_hp = fallback_max_hp
                current_max_hp = fallback_max_hp

            current_hp = getattr(session, "authoritative_current_hp", None)
            if current_hp is None:
                session.authoritative_current_hp = current_max_hp
            else:
                session.authoritative_current_hp = min(max(0, int(current_hp)), current_max_hp)

            print(f"[{session.addr}] [PKT08] Learned clientEntID = {entity_id}")
            _request_client_combat_stats_sync(session)
            if session.current_level == "CraftTown" and getattr(session, "crafttown_building_refresh_pending", False):
                _refresh_crafttown_buildings_on_spawn(session)
                session.crafttown_building_refresh_pending = False

    # Build props
    props = {
        "pos_x": pos_x,
        "pos_y": pos_y,
        "velocity_x": velocity_x,
        "ent_name": ent_name,
        "name": ent_name,
        "team": team,
        "is_player": is_player,
        "render_depth_offset": y_offset,
        "cue_data": cue_data,
        "summoner_id": summoner_id,
        "power_id": power_id,
        "ent_state": ent_state,
        "b_left": b_left,
        "b_running": b_running,
        "b_jumping": b_jumping,
        "b_dropping": b_dropping,
        "b_backpedal": b_backpedal,
    }

    # Was this entity already known in this session?
    is_new_entity = entity_id not in session.entities

    # Update server-side map
    ent_name = props.get("name", f"Entity_{entity_id}")
    
    if not is_player:
        session.client_spawn_confirmed = True
        print(f"[{session.addr}] [PKT08] Client-spawn NPC detected in {session.current_level}: {ent_name} ({entity_id})")
        
        # Check if Boss to trigger UI
        from game_data import get_ent_type
        from globals import send_room_boss_info, send_room_sound
        
        ety = get_ent_type(ent_name)
        rank = ety.get("EntRank") if ety else None
        is_rank_boss = rank == "Boss"
        is_keep_boss = (
            session.current_level == "CraftTownTutorial"
            and ent_name in {"GoblinShamanHood", "IntroGoblinShamanHood"}
        )

        sent_ids = getattr(session, "_boss_info_sent_ids", None)
        if sent_ids is None:
            sent_ids = set()
            session._boss_info_sent_ids = sent_ids

        if is_keep_boss:
            state = getattr(session, "keep_tutorial_state", None)
            if isinstance(state, dict):
                fallback_boss_id = state.get("fallback_boss_id")
                state["boss_entity_seen"] = entity_id
                state["boss_entity_source"] = "client"
                if fallback_boss_id and int(fallback_boss_id) != int(entity_id):
                    fallback_boss_id = int(fallback_boss_id)
                    session.entities.pop(fallback_boss_id, None)
                    from globals import build_destroy_entity_packet

                    session.conn.sendall(build_destroy_entity_packet(fallback_boss_id))

        if (is_rank_boss or is_keep_boss) and entity_id not in sent_ids:
            boss_name = "Ranik, The Geomancer" if is_keep_boss else ent_name
            send_room_boss_info(
                session,
                entity_id,
                boss_name,
                room_id=getattr(session, "current_room_id", 0),
            )
            sent_ids.add(entity_id)

            if is_keep_boss and not getattr(session, "_keep_boss_music_started", False):
                send_room_sound(
                    session,
                    "D02_MoodLoop_GoblinHideout",
                    0.9,
                    room_id=getattr(session, "current_room_id", 0),
                )
                session._keep_boss_music_started = True

    session.entities[entity_id] = props

    if (
        not is_player
        and session.current_level == "CraftTownTutorial"
        and ent_name == "IntroParrot"
        and not getattr(session, "_keep_intro_skit_sent", False)
    ):
        try:
            from globals import build_start_skit_packet
            session.conn.sendall(build_start_skit_packet(entity_id, dialogue_id=0, mission_id=5))
            session._keep_intro_skit_sent = True
        except Exception:
            pass

    if entity_id == session.clientEntID:
        max_hp = int(getattr(session, "authoritative_max_hp", 0) or 0)
        if max_hp > 0:
            props["max_hp"] = max_hp
            props["hp"] = int(getattr(session, "authoritative_current_hp", max_hp) or max_hp)

    level = session.current_level
    level_map = GS.level_entities.setdefault(level, {})

    existing_entry = level_map.get(entity_id, {}) if isinstance(level_map.get(entity_id), dict) else {}
    is_player_name_match = bool(current_name_norm and ent_name_norm == current_name_norm)
    controlled_player = (
        is_player
        or (session.clientEntID is not None and entity_id == session.clientEntID)
        or is_player_name_match
    )
    owner_session = session if controlled_player else existing_entry.get("session")

    level_map[entity_id] = {
        "id": entity_id,
        "kind": "player" if controlled_player else "npc",
        "session": owner_session,
        "props": {
            "id": entity_id,
            "name": ent_name,
            "is_player": is_player,
            "x": int(pos_x),
            "y": int(pos_y),
            "v": int(velocity_x),
            "team": int(team),
            "untargetable": False,
            "render_depth_offset": y_offset,
            "behavior_speed": 0.0,
            "cue_data": cue_data,
            "summonerId": summoner_id or 0,
            "power_id": power_id or 0,
            "entState": ent_state,
            "facing_left": b_left,
            "health_delta": 0,
            "buffs": [],
            "client_spawned": not is_player,
        },
    }

    # ─────────────────────────────
    # spawn non-player entities (pets / minions) for other clients
    # ─────────────────────────────
    if is_new_entity and not is_player:

        ent_dict = {
            "id": entity_id,
            "name": ent_name,
            "is_player": False,
            "x": int(pos_x),
            "y": int(pos_y),
            "v": int(velocity_x),
            "render_depth_offset": y_offset,
            "team": int(team),
            "cue_data": cue_data,
            "summonerId": summoner_id or 0,
            "power_id": power_id or 0,
            "entState": ent_state,
            "facing_left": b_left,
            "health_delta": 0,
            "buffs": [],
        }

        flat_ent = normalize_entity_for_send(ent_dict)
        pkt = Send_Entity_Data(flat_ent)
        framed = struct.pack(">HH", 0x0F, len(pkt)) + pkt

        for other in GS.all_sessions:
            if (
                    other is not session
                    and other.player_spawned
                    and other.current_level == session.current_level
            ):
                other.conn.sendall(framed)
                print(f"[SPAWN] Broadcasted new entity {entity_id} ({ent_name}) → {other.addr}")

    # First-time world load for this player
    if not session.player_spawned:
        session.player_spawned = True
        send_existing_entities_to_joiner(session)
        
        # Re-sync gear to self so client recalculates find stats from runes
        from combat import send_gear_to_self
        send_gear_to_self(session)


        # Broadcast THIS player’s spawn to others
        char = next(
            (c for c in session.char_list if c.get("name") == session.current_character),
            None
        )
        if char:
            ent_dict = build_entity_dict(entity_id, char, props)
            flat_ent = normalize_entity_for_send(ent_dict)
            pkt = Send_Entity_Data(flat_ent)
            framed = struct.pack(">HH", 0x0F, len(pkt)) + pkt
            for other in GS.all_sessions:
                if (
                        other is not session
                        and other.player_spawned
                        and other.current_level == session.current_level
                ):
                    other.conn.sendall(framed)
                    #print(f"[JOIN] Broadcasted Send_Entity_Data for {ent_dict['name']} → {other.addr}")

def ensure_level_npcs(level_name: str, force_reload: bool = False) -> None:
    try:
        from level_config import is_dungeon_level  # local import to avoid circulars
    except Exception:
        is_dungeon_level = lambda _: False

    if level_name in GS.level_entities and not force_reload:
        # Level already loaded — just reset dungeon tracker if needed
        if is_dungeon_level(level_name):
            level_map = GS.level_entities[level_name]
            total_enemies = sum(
                1 for ent in level_map.values()
                if ent.get("kind") == "npc" and ent.get("props", {}).get("team") == 2
            )
            init_dungeon_run(level_name, total_enemies)
            # Reset rewards_granted + HP on all enemies so they can be re-killed
            for ent in level_map.values():
                props = ent.get("props", {})
                if props.get("team") == 2:
                    props.pop("rewards_granted", None)
                    props.pop("hp", None)
        return
    if force_reload and level_name in GS.level_entities:
        del GS.level_entities[level_name]

    npcs = load_npc_data_for_level(level_name)

    if is_dungeon_level(level_name) and level_name != "CraftTown":
        total_enemies = sum(1 for npc in npcs if npc.get("team") == 2)
        if total_enemies > 0:
            init_dungeon_run(level_name, total_enemies)
            # Fresh run: reset kill tracking to avoid stale progress when re-entering
            run = GS.dungeon_runs.get(level_name)
            if run:
                run["killed_ids"] = set()
                run["last_reset"] = time.time()

    level_map = GS.level_entities.setdefault(level_name, {})

    for npc_template in npcs:
        npc_id = allocate_entity_id()

        npc = dict(npc_template)
        npc["id"] = npc_id
        # Seed position fields consistently
        npc.setdefault("x", npc.get("pos_x", npc.get("x", 0.0)))
        npc.setdefault("y", npc.get("pos_y", npc.get("y", 0.0)))
        npc["pos_x"] = npc.get("x", 0.0)
        npc["pos_y"] = npc.get("y", 0.0)

        level_map[npc_id] = {
            "id": npc_id,
            "kind": "npc",
            "session": None,
            "props": npc,
        }




def normalize_entity_for_send(entity: dict) -> dict:
    out = dict(entity)

    cue = entity.get("cue_data", {})
    if cue:
        for key in ("character_name", "DramaAnim", "SleepAnim"):
            val = cue.get(key)
            if val:
                out[key] = val
                if key == "character_name" and val.startswith(","):
                    override_name = val[1:]
                    if override_name:
                        out["name"] = override_name

    out.setdefault("character_name", "")
    out.setdefault("DramaAnim", "")
    out.setdefault("SleepAnim", "")
    return out


def npc_container_to_entity(container: dict) -> dict:
    props = container["props"]
    out = dict(props)
    out["id"] = container["id"]
    out.setdefault("health_delta", 0)
    out.setdefault("buffs", [])
    return out


def allocate_entity_id():
    eid = GS.next_entity_id
    GS.next_entity_id += 1
    return eid
