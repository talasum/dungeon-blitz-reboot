import copy
import hashlib
import json
import os
import secrets
import struct
import threading
import time

from BitBuffer import BitBuffer
from Character import build_login_character_list_bitpacked
from WorldEnter import build_enter_world_packet, Player_Data_Packet
from accounts import get_or_create_user_id, load_accounts, build_popup_packet, is_character_name_taken, load_characters, save_characters
from ai_logic import AI_ENABLED, ensure_ai_loop, run_ai_loop
from bitreader import BitReader
from constants import EntType, load_class_template
from entity import Send_Entity_Data, allocate_entity_id, ensure_level_npcs, normalize_entity_for_send
from globals import SECRET, _level_add, all_sessions, GS, HOST, PORTS, send_quest_progress, reset_dungeon_run, init_dungeon_run, send_npc_dialog, send_mission_added
from level_config import LEVEL_CONFIG, get_spawn_coordinates, send_room_event_start
from socials import get_group_for_session, online_group_members, update_session_group_cache, build_group_update_packet

# Keep empty in production so dungeon NPCs are server-spawned and obey
# server-side movement/combat flags (including no-jump attack behavior).
CLIENT_SPAWN_NPC_LEVELS = {
    "CraftTownTutorial",
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
KEEP_TUTORIAL_BOSS_NAMES = {"GoblinShamanHood", "IntroGoblinShamanHood"}
KEEP_TUTORIAL_BOSS_DISPLAY_NAME = "Ranik, The Geomancer"
KEEP_TUTORIAL_BOSS_SOUND = "D02_MoodLoop_GoblinHideout"
KEEP_TUTORIAL_FALLBACK_BOSS_GRACE_SEC = 2.0
KEEP_TUTORIAL_FALLBACK_CUTSCENE_SEC = 5.9
KEEP_TUTORIAL_FALLBACK_POST_CUTSCENE_DELAY_SEC = 5.0
KEEP_TUTORIAL_FALLBACK_BOARDING_ANIM_SEC = 0.35


def should_client_spawn_npcs(level_name: str, is_dev_client: bool) -> bool:
    if is_dev_client:
        return True
    return level_name in CLIENT_SPAWN_NPC_LEVELS


def _is_dungeon_level_for_runtime(level_name: str) -> bool:
    level_config = LEVEL_CONFIG.get(level_name, ("", 0, 0, False))
    return level_config[3] and level_name != "CraftTown"


def _ensure_keep_tutorial_state(session) -> dict:
    state = getattr(session, "keep_tutorial_state", None)
    if not isinstance(state, dict):
        state = {"phase": 0, "boss_defeated": False}
        session.keep_tutorial_state = state
    return state


def _session_send_npc_spawn(session, npc: dict) -> None:
    flat_npc = normalize_entity_for_send(npc)
    payload = Send_Entity_Data(flat_npc)
    session.conn.sendall(struct.pack(">HH", 0x0F, len(payload)) + payload)
    session.entities[npc["id"]] = dict(npc)


def _session_send_npc_state(session, npc: dict) -> None:
    bb = BitBuffer()
    bb.write_method_4(int(npc["id"]))
    bb.write_method_45(0)
    bb.write_method_45(0)
    bb.write_method_45(0)
    bb.write_method_6(int(npc.get("entState", 0)), 2)
    bb.write_method_15(bool(npc.get("b_left", False)))
    bb.write_method_15(bool(npc.get("b_running", False)))
    bb.write_method_15(bool(npc.get("b_jumping", False)))
    bb.write_method_15(bool(npc.get("b_dropping", False)))
    bb.write_method_15(bool(npc.get("b_backpedal", False)))
    bb.write_method_15(False)
    payload = bb.to_bytes()
    session.conn.sendall(struct.pack(">HH", 0x07, len(payload)) + payload)


def _session_send_set_untargetable(session, entity_id: int, untargetable: bool) -> None:
    bb = BitBuffer()
    bb.write_method_4(int(entity_id))
    bb.write_method_15(bool(untargetable))
    payload = bb.to_bytes()
    session.conn.sendall(struct.pack(">HH", 0xAE, len(payload)) + payload)


def _ensure_npc_cue_data(npc: dict) -> dict:
    cue = npc.get("cue_data", {})
    if not isinstance(cue, dict):
        cue = {}
    cue = dict(cue)
    for key in ("character_name", "DramaAnim", "SleepAnim"):
        value = npc.get(key)
        if value and key not in cue:
            cue[key] = value
    if cue:
        npc["cue_data"] = cue
    return cue


def _classify_crafttown_tutorial_fallback_entities(level_map: dict) -> tuple[int | None, int | None, list[int]]:
    boss_id = None
    boss_dist = None
    last_guy_id = None
    last_guy_x = None
    helper_ids: list[tuple[int, int]] = []

    for eid, ent in level_map.items():
        if not isinstance(ent, dict):
            continue
        props = ent.get("props", {})
        if not isinstance(props, dict) or int(props.get("team", 0)) != 2:
            continue

        name = str(props.get("name", ""))
        x = int(props.get("x", props.get("pos_x", 0)))
        y = int(props.get("y", props.get("pos_y", 0)))

        if name in KEEP_TUTORIAL_BOSS_NAMES:
            dist = abs(x - 49) + abs(y - 1459)
            if boss_dist is None or dist < boss_dist:
                boss_dist = dist
                boss_id = int(eid)
            continue

        if name == "GoblinShamanHood":
            dist = abs(x - 49) + abs(y - 1459)
            if boss_dist is None or dist < boss_dist:
                boss_dist = dist
                boss_id = int(eid)
            continue

        drama_anim = ""
        cue = props.get("cue_data", {})
        if isinstance(cue, dict):
            drama_anim = str(cue.get("DramaAnim", ""))
        if not drama_anim:
            drama_anim = str(props.get("DramaAnim", ""))

        if name == "GoblinDagger" and drama_anim == "Board":
            helper_ids.append((x, int(eid)))
            continue

        if name == "GoblinDagger" and int(props.get("entState", 0)) != 2:
            if last_guy_x is None or x > last_guy_x:
                last_guy_x = x
                last_guy_id = int(eid)

    helper_ids.sort()
    return last_guy_id, boss_id, [eid for _, eid in helper_ids]


def _ensure_crafttown_tutorial_fallback_hostiles(level_map: dict) -> None:
    has_hostiles = any(
        isinstance(ent, dict)
        and isinstance(ent.get("props"), dict)
        and int(ent["props"].get("team", 0)) == 2
        for ent in level_map.values()
    )
    if has_hostiles:
        return

    json_path = os.path.join(os.path.dirname(__file__), "world_npcs", "CraftTownTutorial.json")
    with open(json_path, "r") as file:
        data = json.load(file)

    for npc_template in data:
        if int(npc_template.get("team", 0)) != 2:
            continue
        npc_id = allocate_entity_id()
        npc = dict(npc_template)
        npc["id"] = npc_id
        npc.setdefault("x", npc.get("pos_x", npc.get("x", 0)))
        npc.setdefault("y", npc.get("pos_y", npc.get("y", 0)))
        npc["pos_x"] = npc.get("x", 0)
        npc["pos_y"] = npc.get("y", 0)
        _ensure_npc_cue_data(npc)
        level_map[npc_id] = {
            "id": npc_id,
            "kind": "npc",
            "session": None,
            "props": npc,
        }


def _prepare_crafttown_tutorial_fallback_entities(level_map: dict) -> tuple[int | None, int | None, list[int]]:
    last_guy_id, boss_id, helper_ids = _classify_crafttown_tutorial_fallback_entities(level_map)

    if last_guy_id is not None:
        last_guy_props = level_map[last_guy_id]["props"]
        last_guy_props["character_name"] = "am_LastGuy"
        cue = _ensure_npc_cue_data(last_guy_props)
        cue["character_name"] = "am_LastGuy"

    if boss_id is not None:
        boss_props = level_map[boss_id]["props"]
        boss_props["name"] = "IntroGoblinShamanHood"
        boss_props["untargetable"] = True
        boss_props["entState"] = 2
        boss_props["character_name"] = ",IntroGoblinShamanHood"
        cue = _ensure_npc_cue_data(boss_props)
        cue["character_name"] = ",IntroGoblinShamanHood"

    for helper_id in helper_ids:
        helper_props = level_map[helper_id]["props"]
        helper_props["untargetable"] = True
        helper_props["entState"] = 2
        helper_props["DramaAnim"] = "Board"
        cue = _ensure_npc_cue_data(helper_props)
        cue.setdefault("DramaAnim", "Board")

    return last_guy_id, boss_id, helper_ids


def _spawn_crafttown_tutorial_fallback(session, force_reload: bool) -> None:
    level_name = session.current_level
    ensure_level_npcs(level_name, force_reload=force_reload)
    level_map = GS.level_entities.setdefault(level_name, {})
    _ensure_crafttown_tutorial_fallback_hostiles(level_map)
    last_guy_id, boss_id, helper_ids = _prepare_crafttown_tutorial_fallback_entities(level_map)

    if _is_dungeon_level_for_runtime(level_name):
        reset_dungeon_run(level_name, user_id=session.user_id)
        session.current_char_dict["questTrackerState"] = 0
        send_quest_progress(session, 0)

    state = _ensure_keep_tutorial_state(session)
    state.update(
        {
            "server_fallback": True,
            "fallback_intro_started": False,
            "fallback_waves_started": False,
            "fallback_last_guy_id": last_guy_id,
            "fallback_boss_id": boss_id,
            "fallback_helper_ids": helper_ids,
            "boss_entity_seen": None,
            "boss_entity_source": None,
        }
    )

    for ent in level_map.values():
        if ent.get("kind") != "npc":
            continue
        npc = ent.get("props", {})
        if not isinstance(npc, dict):
            continue
        npc_id = int(npc.get("id", 0))
        if npc_id == boss_id or npc_id in helper_ids:
            continue
        _session_send_npc_spawn(session, npc)

    if not getattr(session, "_keep_intro_skit_sent", False):
        parrot_id = next(
            (
                eid
                for eid, ent in level_map.items()
                if isinstance(ent, dict)
                and isinstance(ent.get("props"), dict)
                and ent.get("props", {}).get("name") == "IntroParrot"
            ),
            None,
        )
        if parrot_id is not None:
            from globals import build_start_skit_packet

            session.conn.sendall(build_start_skit_packet(parrot_id, dialogue_id=0, mission_id=5))
            session._keep_intro_skit_sent = True

    print(
        f"[Login] CraftTownTutorial fallback armed: last_guy={last_guy_id}, "
        f"boss={boss_id}, helpers={len(helper_ids)}"
    )


def _activate_crafttown_tutorial_fallback_enemy(session, entity_id: int) -> None:
    level_map = GS.level_entities.get(session.current_level, {})
    entry = level_map.get(entity_id, {})
    npc = entry.get("props", {}) if isinstance(entry, dict) else {}
    if not isinstance(npc, dict):
        return

    npc["untargetable"] = False
    npc["entState"] = 0
    session.entities.setdefault(entity_id, dict(npc))
    session.entities[entity_id]["untargetable"] = False
    session.entities[entity_id]["entState"] = 0
    _session_send_set_untargetable(session, entity_id, False)
    _session_send_npc_state(session, npc)


def _start_crafttown_tutorial_fallback_waves(session, state: dict) -> None:
    if state.get("fallback_waves_started"):
        return
    state["fallback_waves_started"] = True

    def _worker():
        level_name = session.current_level
        helper_ids = list(state.get("fallback_helper_ids", []))
        level_map = GS.level_entities.get(level_name, {})
        active_helper_ids: list[int] = []
        for helper_id in helper_ids:
            if not getattr(session, "running", False):
                return
            if session.current_level != level_name or state.get("boss_defeated"):
                return
            entry = level_map.get(helper_id, {})
            helper = entry.get("props", {}) if isinstance(entry, dict) else {}
            if not isinstance(helper, dict):
                continue
            _session_send_npc_spawn(session, helper)
            active_helper_ids.append(helper_id)

        if not active_helper_ids:
            return

        time.sleep(KEEP_TUTORIAL_FALLBACK_BOARDING_ANIM_SEC)
        if session.current_level != level_name or state.get("boss_defeated"):
            return

        for helper_id in active_helper_ids:
            _activate_crafttown_tutorial_fallback_enemy(session, helper_id)

    threading.Thread(target=_worker, daemon=True).start()


def maybe_start_crafttown_tutorial_fallback_intro(session) -> None:
    state = _ensure_keep_tutorial_state(session)
    if not state.get("server_fallback") or state.get("fallback_intro_started"):
        return
    if state.get("boss_defeated"):
        return

    state["fallback_intro_started"] = True

    def _worker():
        level_name = session.current_level
        started_at = time.monotonic()
        while time.monotonic() - started_at < KEEP_TUTORIAL_FALLBACK_BOSS_GRACE_SEC:
            if not getattr(session, "running", False):
                return
            if session.current_level != level_name or state.get("boss_defeated"):
                return
            if state.get("boss_entity_source") == "client":
                return
            time.sleep(0.1)

        boss_id = state.get("fallback_boss_id")
        if boss_id is None:
            return

        level_map = GS.level_entities.get(level_name, {})
        entry = level_map.get(boss_id, {})
        boss = entry.get("props", {}) if isinstance(entry, dict) else {}
        if not isinstance(boss, dict):
            return

        _session_send_npc_spawn(session, boss)
        state["boss_entity_seen"] = boss_id
        state["boss_entity_source"] = "fallback"

        from globals import send_room_boss_info, send_room_sound

        send_room_boss_info(
            session,
            boss_id,
            KEEP_TUTORIAL_BOSS_DISPLAY_NAME,
            room_id=getattr(session, "current_room_id", 0),
        )
        if not getattr(session, "_keep_boss_music_started", False):
            send_room_sound(
                session,
                KEEP_TUTORIAL_BOSS_SOUND,
                0.9,
                room_id=getattr(session, "current_room_id", 0),
            )
            session._keep_boss_music_started = True

        time.sleep(KEEP_TUTORIAL_FALLBACK_CUTSCENE_SEC)
        if session.current_level != level_name or state.get("boss_defeated"):
            return
        if state.get("boss_entity_source") == "client":
            return

        time.sleep(KEEP_TUTORIAL_FALLBACK_POST_CUTSCENE_DELAY_SEC)
        if session.current_level != level_name or state.get("boss_defeated"):
            return
        if state.get("boss_entity_source") == "client":
            return

        _activate_crafttown_tutorial_fallback_enemy(session, boss_id)
        _start_crafttown_tutorial_fallback_waves(session, state)

    threading.Thread(target=_worker, daemon=True).start()


def cleanup_crafttown_tutorial_fallback(session) -> None:
    state = _ensure_keep_tutorial_state(session)
    helper_ids = list(state.get("fallback_helper_ids", []))
    if not helper_ids:
        return

    from globals import build_destroy_entity_packet

    level_map = GS.level_entities.get(session.current_level, {})
    for entity_id in helper_ids:
        session.entities.pop(entity_id, None)
        if level_map and entity_id in level_map:
            del level_map[entity_id]
        pkt = build_destroy_entity_packet(entity_id)
        session.conn.sendall(pkt)


def _spawn_server_level_npcs_for_session(session, force_reload: bool):
    ensure_level_npcs(session.current_level, force_reload=force_reload)

    if _is_dungeon_level_for_runtime(session.current_level):
        reset_dungeon_run(session.current_level, user_id=session.user_id)

    run_key = (session.current_level, session.user_id) if session.user_id else session.current_level
    run = GS.dungeon_runs.get(run_key)
    if run:
        kills = len(run.get("killed_ids", []))
        total = run.get("total", 0)
        percent = min(100, int((kills * 100) / total)) if total else 0
        if kills == 0:
            percent = 0
        session.current_char_dict["questTrackerState"] = percent
        send_quest_progress(session, percent)
        print(f"[DEBUG] Dungeon Spawn: Level={session.current_level} Kills={kills} Total={total} Percent={percent}%")

    level_map = GS.level_entities.get(session.current_level, {})
    npcs = [
        ent["props"]
        for ent in level_map.values()
        if ent["kind"] == "npc"
    ]
    for npc in npcs:
        _session_send_npc_spawn(session, npc)

    # CraftTownTutorial fallback: if NPCs are server-spawned, emit the intro parrot skit
    # because the client-side 0x08 hook will not run in this path.
    if (
        session.current_level == "CraftTownTutorial"
        and not getattr(session, "_keep_intro_skit_sent", False)
    ):
        level_map = GS.level_entities.get("CraftTownTutorial", {})
        parrot_id = next(
            (
                eid for eid, ent in level_map.items()
                if isinstance(ent, dict)
                and isinstance(ent.get("props"), dict)
                and ent.get("props", {}).get("name") == "IntroParrot"
            ),
            None,
        )
        if parrot_id is not None:
            from globals import build_start_skit_packet
            session.conn.sendall(build_start_skit_packet(parrot_id, dialogue_id=0, mission_id=5))
            session._keep_intro_skit_sent = True

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
        if level_name == "CraftTownTutorial":
            _spawn_crafttown_tutorial_fallback(session, force_reload=False)
        else:
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
    GS.pending_extended[tk] = True

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
        GS.pending_extended[tk] = True
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
    session.max_hp_sync_level = None
    session.pending_orb_heal = None

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

    token_requests_extended = bool(GS.pending_extended.pop(token, False))
    send_extended_block = bool(first_login) or token_requests_extended

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

    session.crafttown_building_refresh_pending = (target_level == "CraftTown")

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
    session._boss_info_sent_ids = set()
    session._keep_boss_music_started = False
    session._keep_intro_skit_sent = False
    session._keep_room_events_started = set()
    session.current_room_id = 0

    # Client-spawn mode (dev client or explicit level override)
    if use_client_spawn_npcs:
        print(f"[Login] Skipping server NPC spawn for {session.current_level} (client-spawn mode).")
        is_dungeon_level = _is_dungeon_level_for_runtime(session.current_level)
        if is_dungeon_level:
            # Client will spawn NPCs; start tracker at 0 and let kills recompute totals from live entities.
            init_dungeon_run(session.current_level, 0, user_id=session.user_id)
            session.current_char_dict["questTrackerState"] = 0
            send_quest_progress(session, 0)
            # Some clients may not emit NPC 0x08 spawns for dungeon maps in non-dev mode.
            # Fallback keeps the dungeon playable instead of leaving it empty.
            _start_client_spawn_fallback(session, force_reload=is_dungeon)
    else:
        _spawn_server_level_npcs_for_session(session, force_reload=is_dungeon)

    # Initial Room Event Start for TutorialDungeon to trigger client-side scripts
    if session.current_level == "TutorialDungeon":
        # Try triggering Room 0 and Room 1 to cover bases
        send_room_event_start(session, 0, True)
        send_room_event_start(session, 1, True)
        # Send initial parrot dialogue (Pecky)
        send_npc_dialog(session, 384606, "Squawk! Goblins! Goblins everywhere! Help Pecky!")
        print(f"[{session.addr}] Sent Room Event Start and Parrot Chat for TutorialDungeon")

    if session.current_level == "TutorialBoat":
        send_room_event_start(session, 0, True)
        send_room_event_start(session, 1, True)

    # CraftTownTutorial (Keep clearing for "I Claim This Keep" / mission 5)
    if session.current_level == "CraftTownTutorial":
        from constants import Mission
        from Commands import _can_start_mission, _persist_char_missions, _set_mission_state
        from globals import build_start_skit_packet
        
        # Prime the first two tutorial rooms so initial cutscenes/scripts fire.
        # Room 7 contains the boss quest completion trigger, so we don't start it here.
        send_room_event_start(session, 0, True)
        send_room_event_start(session, 1, True)

        # Ensure mission 5 is truly active on server for this character.
        # Players can be routed into CraftTownTutorial before accepting from mayor,
        # which blocks completion/progression logic that expects state=InProgress.
        char = session.current_char_dict or {}
        m5_state = int((char.get("missions", {}).get("5") or {}).get("state", Mission.const_213))
        if m5_state == Mission.const_213 and _can_start_mission(char, 5):
            _set_mission_state(char, 5, Mission.const_58, curr_count=0)
            _persist_char_missions(session, char)
            send_mission_added(session, 5)
            print(f"[{session.addr}] Activated Mission 5 (ClearYourHouse) on CraftTownTutorial entry")

        # Find the closest IntroParrot entity by name (IDs are dynamically allocated)
        level_map = GS.level_entities.get("CraftTownTutorial", {})
        player_x = int(round(new_x))
        player_y = int(round(new_y))
        parrot_id = None
        best_dist = None
        for eid, ent in level_map.items():
            props = ent.get("props", {}) if isinstance(ent, dict) else {}
            if props.get("name") != "IntroParrot":
                continue
            ex = int(props.get("x", props.get("pos_x", 0)))
            ey = int(props.get("y", props.get("pos_y", 0)))
            dist = abs(ex - player_x) + abs(ey - player_y)
            if best_dist is None or dist < best_dist:
                parrot_id = eid
                best_dist = dist

        if parrot_id:
            # Use build_start_skit_packet (0x7B) for animated dialog with NPC
            # facing player and performing skit animations, not just text bubble
            pkt = build_start_skit_packet(parrot_id, dialogue_id=0, mission_id=5)
            session.conn.sendall(pkt)
            print(f"[{session.addr}] Triggered parrot skit (entity {parrot_id}) for CraftTownTutorial")
        else:
            print(f"[{session.addr}] Warning: IntroParrot not found in CraftTownTutorial level_entities")

        session.keep_tutorial_state = {"phase": 0, "boss_defeated": False}
        print(f"[{session.addr}] CraftTownTutorial mission 5 state sent")
