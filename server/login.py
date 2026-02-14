import copy
import hashlib
import json
import os
import secrets
import struct
import threading
import time

from Character import build_login_character_list_bitpacked
from WorldEnter import build_enter_world_packet, Player_Data_Packet
from accounts import get_or_create_user_id, load_accounts, build_popup_packet, is_character_name_taken, load_characters, save_characters
from ai_logic import AI_ENABLED, ensure_ai_loop, run_ai_loop
from bitreader import BitReader
from constants import EntType, load_class_template
from entity import Send_Entity_Data, ensure_level_npcs, normalize_entity_for_send
from globals import SECRET, _level_add, all_sessions, GS, HOST, PORTS, send_quest_progress, reset_dungeon_run, init_dungeon_run
from level_config import LEVEL_CONFIG, get_spawn_coordinates
from socials import get_group_for_session, online_group_members, update_session_group_cache, build_group_update_packet

# Keep empty in production so dungeon NPCs are server-spawned and obey
# server-side movement/combat flags (including no-jump attack behavior).
CLIENT_SPAWN_NPC_LEVELS = {
    "CraftTown",
    "NewbieRoad", "NewbieRoadHard",
    "SwampRoadNorth", "SwampRoadNorthHard",
    "SwampRoadConnection", "SwampRoadConnectionHard",
    "BridgeTown", "BridgeTownHard",
    "CemeteryHill", "CemeteryHillHard",
    "OldMineMountain", "OldMineMountainHard",
    "EmeraldGlades", "EmeraldGladesHard",
    "Castle", "CastleHard",
    "ShazariDesert", "ShazariDesertHard",
    "JadeCity", "JadeCityHard"
}
CLIENT_SPAWN_FALLBACK_SEC = 5.0

def should_client_spawn_npcs(level_name: str, is_dev_client: bool) -> bool:
    if is_dev_client:
        return True
    return level_name in CLIENT_SPAWN_NPC_LEVELS

def _is_dungeon_level_for_runtime(level_name: str) -> bool:
    level_config = LEVEL_CONFIG.get(level_name, ("", 0, 0, False))
    return level_config[3] and level_name != "CraftTown"

def _spawn_server_level_npcs_for_session(session, force_reload: bool):
    ensure_level_npcs(session.current_level, force_reload=force_reload)

    if _is_dungeon_level_for_runtime(session.current_level):
        reset_dungeon_run(session.current_level)

    run = GS.dungeon_runs.get(session.current_level)
    if run:
        kills = len(run.get("killed_ids", []))
        total = run.get("total", 0)
        percent = min(100, int((kills * 100) / total)) if total else 0
        if kills == 0:
            percent = 0
        session.current_char_dict["questTrackerState"] = percent
        send_quest_progress(session, percent)

    level_map = GS.level_entities.get(session.current_level, {})
    npcs = [
        ent["props"]
        for ent in level_map.values()
        if ent["kind"] == "npc"
    ]
    for npc in npcs:
        flat_npc = normalize_entity_for_send(npc)
        payload = Send_Entity_Data(flat_npc)
        session.conn.sendall(
            struct.pack(">HH", 0x0F, len(payload)) + payload
        )
        session.entities[npc["id"]] = npc

def _start_client_spawn_fallback(session, force_reload: bool):
    level_name = session.current_level

    def _worker():
        time.sleep(CLIENT_SPAWN_FALLBACK_SEC)
        if not getattr(session, "running", False):
            return
        if session.current_level != level_name:
            return
        if getattr(session, "client_spawn_confirmed", False):
            return

        print(f"[Login] No client NPC spawn packets detected for {level_name}; falling back to server NPC spawns.")
        _spawn_server_level_npcs_for_session(session, force_reload=force_reload)
        if AI_ENABLED:
            ensure_ai_loop(level_name, run_ai_loop)

    threading.Thread(target=_worker, daemon=True).start()

def _purge_same_character_ghosts(active_session, user_id, char_name):
    for level_name, level_map in list(GS.level_entities.items()):
        if not isinstance(level_map, dict):
            continue
        stale_ids = []
        for eid, ent in level_map.items():
            if not isinstance(ent, dict):
                continue
            props = ent.get("props") if isinstance(ent.get("props"), dict) else {}
            if ent.get("kind") == "player" and props.get("name") == char_name:
                stale_ids.append(eid)
        for eid in stale_ids:
            level_map.pop(eid, None)

    for other in list(GS.all_sessions):
        if other is active_session:
            continue
        if int(getattr(other, "user_id", -1) or -1) != int(user_id):
            continue
        if getattr(other, "current_character", None) != char_name:
            continue

        if getattr(other, "current_level", None):
            level_sessions = GS.level_registry.get(other.current_level)
            if level_sessions and other in level_sessions:
                level_sessions.discard(other)

        for tk, sess in list(GS.session_by_token.items()):
            if sess is other:
                GS.session_by_token.pop(tk, None)

        try:
            other.conn.close()
        except Exception:
            pass

        other.running = False
        other.authenticated = False
        if other in GS.all_sessions:
            GS.all_sessions.remove(other)

def handle_login_version(session, data):
    br = BitReader(data[4:])
    client_version = br.read_method_9()

    sid = secrets.randbelow(1 << 16)
    sid_bytes = sid.to_bytes(2, "big")
    digest = hashlib.md5(sid_bytes + SECRET).hexdigest()[:12]

    challenge = f"{sid:04x}{digest}"
    session.challenge_str = challenge

    utf_bytes = challenge.encode("utf-8")
    payload = struct.pack(">H", len(utf_bytes)) + utf_bytes
    pkt = struct.pack(">HH", 0x12, len(payload)) + payload

    session.conn.sendall(pkt)


def handle_login_create(session, data):
    br = BitReader(data[4:])
    client_facebook_id = br.read_method_26()
    client_kongregate_id = br.read_method_26()
    email = br.read_method_26().strip().lower()
    password = br.read_method_26()
    legacy_auth_key = br.read_method_26()

    session.user_id = int(get_or_create_user_id(email))
    session.authenticated = True
    session.char_list = load_characters(session.user_id)

    pkt = build_login_character_list_bitpacked(session.user_id, session.char_list)
    session.conn.sendall(pkt)

    print(f"[{session.addr}] [0x13] Login/Create OK for {email} → {len(session.char_list)} characters")

def handle_login_authenticate(session, data):
    br = BitReader(data[4:])
    client_facebook_id = br.read_method_26()
    client_kongregate_id = br.read_method_26()
    email = br.read_method_26().strip().lower()
    encrypted_password = br.read_method_26()
    legacy_auth_key = br.read_method_26()

    accounts = load_accounts()
    user_id = accounts.get(email)

    if not user_id:
        session.conn.sendall(
            build_popup_packet("Account not found", disconnect=True)
        )
        print(f"[{session.addr}] [0x14] Login failed — no account for {email}")
        return

    session.user_id = user_id
    session.char_list = load_characters(session.user_id)
    session.authenticated = True

    pkt = build_login_character_list_bitpacked(session.user_id, session.char_list)
    session.conn.sendall(pkt)

    print(f"[{session.addr}] [0x14] Login success for {email} → user_id={user_id}, {len(session.char_list)} chars")

def handle_login_character_create(session, data):
    br = BitReader(data[4:])
    name = br.read_method_26()
    class_name = br.read_method_26()
    gender = br.read_method_26()
    head = br.read_method_26()
    hair = br.read_method_26()
    mouth = br.read_method_26()
    face = br.read_method_26()
    hair_color = br.read_method_20(EntType.CHAR_COLOR_BITSTOSEND)
    skin_color = br.read_method_20(EntType.CHAR_COLOR_BITSTOSEND)
    shirt_color = br.read_method_20(EntType.CHAR_COLOR_BITSTOSEND)
    pant_color = br.read_method_20(EntType.CHAR_COLOR_BITSTOSEND)

    if is_character_name_taken(name):
        session.conn.sendall(build_popup_packet(
            "Character name is unavailable. Please choose a new name.",
            disconnect=False
        ))
        print(f"[{session.addr}] [0x17] Name taken: {name}")
        return

    base_template = load_class_template(class_name)
    new_char = copy.deepcopy(base_template)
    new_char.update({
        "name": name,
        "class": class_name,
        "gender": gender,
        "headSet": head,
        "hairSet": hair,
        "mouthSet": mouth,
        "faceSet": face,
        "hairColor": hair_color,
        "skinColor": skin_color,
        "shirtColor": shirt_color,
        "pantColor": pant_color,
    })

    session.char_list.append(new_char)
    save_characters(session.user_id, session.char_list)

    current_level = new_char["CurrentLevel"]["name"]
    prev_level = new_char["PreviousLevel"]["name"]

    tk = session.ensure_token(new_char, target_level=current_level, previous_level=prev_level)
    session.transfer_token = tk
    GS.session_by_token[tk] = session

    level_config = LEVEL_CONFIG.get(current_level, ("LevelsNR.swf/a_Level_NewbieRoad", 1, 1, False))

    pkt = build_enter_world_packet(
        transfer_token=tk,
        old_level_id=0,
        old_swf="",
        has_old_coord=False,
        old_x=0,
        old_y=0,
        host=HOST,
        port=PORTS[0],
        new_level_swf=level_config[0],
        new_map_lvl=level_config[1],
        new_base_lvl=level_config[2],
        new_internal=current_level,
        new_moment="",
        new_alter="",
        new_is_dungeon=level_config[3],
        new_has_coord=False,
        new_x=0,
        new_y=0,
        char=new_char,
    )

    session.conn.sendall(pkt)
    GS.pending_world[tk] = (new_char, current_level, prev_level)

    print(f"[{session.addr}] [0x17] Character '{name}' created → entering {current_level} (tk={tk})")

def handle_character_select(session, data):
    br = BitReader(data[4:])
    name = br.read_method_26()

    for c in session.char_list:
        if c["name"] != name:
            continue

        session.current_character = name
        session.current_char_dict = c

        current_level = c.get("CurrentLevel", {}).get("name", "CraftTown")
        prev_level = c.get("PreviousLevel", {}).get("name", "NewbieRoad")
        session.current_level = current_level

        tk = session.ensure_token(c, target_level=current_level, previous_level=prev_level)
        session.transfer_token = tk
        GS.session_by_token[tk] = session

        level_config = LEVEL_CONFIG.get(
            current_level, ("LevelsNR.swf/a_Level_NewbieRoad", 1, 1, False)
        )

        is_hard = current_level.endswith("Hard")
        new_moment = "Hard" if is_hard else ""
        new_alter = "Hard" if is_hard else ""

        pkt = build_enter_world_packet(
            transfer_token=tk,
            old_level_id=0,
            old_swf="",
            has_old_coord=False,
            old_x=0,
            old_y=0,
            host=HOST,
            port=PORTS[0],
            new_level_swf=level_config[0],
            new_map_lvl=level_config[1],
            new_base_lvl=level_config[2],
            new_internal=current_level,
            new_moment=new_moment,
            new_alter=new_alter,
            new_is_dungeon=level_config[3],
            new_has_coord=False,
            new_x=0,
            new_y=0,
            char=c,
        )

        session.conn.sendall(pkt)
        GS.pending_world[tk] = (c, current_level, prev_level)
        print(f"[{session.addr}] [0x16] Transfer begin: {name}, tk={tk}, level={current_level}")

def handle_gameserver_login(session, data):
    br = BitReader(data[4:])
    token        = br.read_method_9()
    Level_Swf_name = br.read_method_26()
    first_login   = br.read_method_15()
    is_dev_client  = br.read_method_15()

    entry = GS.pending_world.get(token)
    if entry is None:
        key = GS.token_char.get(token)
        if not key:
            for k, tk in GS.char_tokens.items():
                if tk == token:
                    key = k
                    GS.token_char[token] = k
                    break
        if key:
            mapped_user_id, mapped_char_name = key

            # Reject token/user mismatches if this session is already authenticated.
            if session.user_id and int(session.user_id) != int(mapped_user_id):
                print(f"[{session.addr}] Invalid token {token}: user mismatch ({session.user_id} != {mapped_user_id})")
                return

            chars = load_characters(mapped_user_id)
            recovered_char = next((c for c in chars if c.get("name") == mapped_char_name), None)
            if recovered_char:
                target_level = recovered_char.get("CurrentLevel", {}).get("name", "CraftTown")
                previous_level = recovered_char.get("PreviousLevel", {}).get("name", "NewbieRoad")
                entry = (recovered_char, target_level, previous_level)
                GS.pending_world[token] = entry
                print(f"[{session.addr}] Recovered token {token} for {mapped_char_name} (pending_world miss)")

        if entry is None:
            print(f"[{session.addr}] Invalid token {token}, pending_world size={len(GS.pending_world)}")
            return

    # expect (char, target_level, previous_level)
    char, target_level, previous_level = entry

    # Resolve user_id from token_char if needed
    if not session.user_id:
        key = GS.token_char.get(token)
        if not key:
            print(f"[{session.addr}] Warning: could not resolve user_id for token {token}")
            return
        session.user_id = key[0]

    session.current_character = char["name"]
    session.current_char_dict = char
    session.current_level     = target_level

    _purge_same_character_ghosts(session, session.user_id, session.current_character)

    # Dungeon entry level
    is_dungeon = LEVEL_CONFIG.get(target_level, (None, None, None, False))[3]
    session.entry_level = previous_level if is_dungeon else None

    session.transfer_token = token
    session.authenticated = True
    GS.current_characters[session.user_id] = session.current_character
    GS.session_by_token[token] = session
    _level_add(target_level, session)

    # Load character list from disk and use the fresh data instead of stale in-memory char
    session.char_list = load_characters(session.user_id)
    
    # Find the character in the freshly loaded list (contains latest saved XP/level)
    fresh_char = next((c for c in session.char_list if c.get("name") == char["name"]), None)
    if fresh_char:
        char = fresh_char  # Use fresh data from disk
    else:
        # Character not found in disk, add it (new character case)
        session.char_list.append(char)
        save_characters(session.user_id, session.char_list)
    
    # Update session to point to the fresh character
    session.current_char_dict = char
    GS.pending_world.pop(token, None)

    # Spawn point
    new_x, new_y, new_has_coord = get_spawn_coordinates(char, previous_level, target_level)

    # Store token mapping (needed by client for entType etc.)
    GS.used_tokens[token] = (char, target_level, previous_level)

    #TODO...
    #level_config = LEVEL_CONFIG.get(target_level, ("", 1, 1, False))
    #bonus_levels = level_config[2]
    bonus_levels = 0

    send_extended_block = bool(first_login) or (not getattr(session, "sent_initial_extended_data", False))

    welcome = Player_Data_Packet(
        char,
        transfer_token=token,
        hp_scaling=0,
        bonus_levels=bonus_levels,
        target_level=target_level,
        new_x=int(round(new_x)),
        new_y=int(round(new_y)),
        new_has_coord=new_has_coord,
        send_extended=send_extended_block,
    )

    session.conn.sendall(welcome)
    session.sent_initial_extended_data = True

    gid, group = get_group_for_session(session)
    if gid and group:
        members = online_group_members(group, all_sessions)
        update_session_group_cache(gid, members)
        pkt = build_group_update_packet(members)
        for member, _ in members:
            member.conn.sendall(pkt)

    #print(f"[{session.addr}] Welcome: {char['name']} (token {token})")

    use_client_spawn_npcs = should_client_spawn_npcs(session.current_level, is_dev_client)
    print(f"[DEBUG] Level='{session.current_level}', Dev={is_dev_client} -> UseClientSpawn={use_client_spawn_npcs}")
    if not use_client_spawn_npcs and session.current_level == "OldMineMountain":
         print(f"[DEBUG] '{session.current_level}' NOT found in {CLIENT_SPAWN_NPC_LEVELS}")

    session.client_spawn_confirmed = False

    if AI_ENABLED and not use_client_spawn_npcs:
        ensure_ai_loop(session.current_level, run_ai_loop)
    elif AI_ENABLED:
        print(f"[Login] Client-spawn NPC mode enabled for {session.current_level}; skipping server AI loop.")
    else:
        pass

    # Clear per-session dedupe so loot/XP work on every zone entry
    session.processed_reward_sources = set()
    session.granted_xp_targets = set()

    # Client-spawn mode (dev client or explicit level override)
    if use_client_spawn_npcs:
        print(f"[Login] Skipping server NPC spawn for {session.current_level} (client-spawn mode).")
        is_dungeon_level = _is_dungeon_level_for_runtime(session.current_level)
        if is_dungeon_level:
            # Client will spawn NPCs; start tracker at 0 and let kills recompute totals from live entities.
            init_dungeon_run(session.current_level, 0)
            session.current_char_dict["questTrackerState"] = 0
            send_quest_progress(session, 0)
        # Some clients may not emit NPC 0x08 spawns for this map in non-dev mode.
        # Fallback keeps the dungeon playable instead of leaving it empty.
        _start_client_spawn_fallback(session, force_reload=is_dungeon)
    else:
        _spawn_server_level_npcs_for_session(session, force_reload=is_dungeon)
