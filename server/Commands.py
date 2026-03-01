import json
import os
import struct
import random
import re
import threading
import time

from bitreader import BitReader
from constants import GearType, class_3, PowerType, Game, class_119, PET_TYPES, get_egg_id, Entity, Mission
from BitBuffer import BitBuffer
from globals import build_start_skit_packet
from missions import get_mission_extra, get_mission_id_by_name, get_mission_def
from accounts import save_characters
from globals import send_gold_reward, send_gear_reward, send_hp_update, send_entity_heal, send_material_reward, GS, send_npc_dialog, send_consumable_reward, send_charm_reward, send_mount_reward, send_dye_reward, send_new_pet_packet, get_npc_props
from game_data import get_random_gear_id
from data.npc_chats import NPC_CHATS

# ── SPECIAL STORY NPCs ──
# These NPCs have unique sequential dialog that should NEVER be replaced with generic NPC chat.
# They form part of a narrative sequence and must maintain story integrity.
# Dialog starters match their placement:
#   - lubu: "Third Place, LuBu."
#   - clintt: "First Place, Clintt."
#   - purplered: "First Place, PurpleRed."
#   - jeromelin: "Fourth Place, JeromeLin."
LOCKED_HALLOWEEN_STATUE_DIALOGS = {
    "clintt": (
        "First Place, Clintt.",
        "Her mastery of magic...",
        "And prowess with a staff.",
        "Shamed the Green Knight...",
        "And gave her the last laugh.",
    ),
    "purplered": (
        "First Place, PurpleRed.",
        "With arcane power and skill...",
        "The Green Knight did she slay.",
        "Now Purple and Red...",
        "Are the colors of the day.",
    ),
    "lubu": (
        "Third Place, LuBu.",
        "With divine might in his arms...",
        "And holy vengeance in his swing...",
        "LuBu cut down the Green Knight.",
        "For glory and his King.",
    ),
    "jeromelin": (
        "Fourth Place, JeromeLin.",
        "From the shadows he struck...",
        "His blade quick and true.",
        "JeromeLin beat the Green Knight...",
        "Many more time than did you.",
    ),
}
STORY_NPCS = ["clintt", "lubu", "purplered", "jeromelin"]
STORY_NPC_LEVEL_PREFIX = "swamproadnorth"
WORLD_NPCS_DIR = os.path.join(os.path.dirname(__file__), "world_npcs")
STORY_NPC_ALIASES = {
    "specialhalloweenstatuethird": "lubu",
    "specialhalloweenstatuethirdhard": "lubu",
    "specialhalloweenstatuefirst": "clintt",
    "specialhalloweenstatuefirsthard": "clintt",
    "specialhalloweenstatuesecond": "purplered",
    "specialhalloweenstatuesecondhard": "purplered",
    "specialhalloweenstatuefourth": "jeromelin",
    "specialhalloweenstatuefourthhard": "jeromelin",
}
STORY_STATUE_RELATIVE_INDICES = {
    27: "lubu",
    31: "purplered",
    32: "clintt",
    33: "jeromelin",
}
STORY_STATUE_TIEBREAK = {
    "clintt": 0,
    "purplered": 1,
    "lubu": 2,
    "jeromelin": 3,
}

# ── GLOBAL STORY NPC STATE ──
# Stores dialog history for Story NPCs per CHARACTER (NOT per level).
# This ensures the sequence survives zone/level changes.
# Format: { "char_id": { "npc_key": ["line1", "line2", ...] } }
# When a player changes zones, their character_id stays the same, so history is preserved.
GLOBAL_STORY_NPC_HISTORY = {}

# Tracks the next dialogue index per Story NPC per character.
# Format: { "char_id": { "npc_key": next_index } }
# Story NPC lines do NOT cycle back to the start.
GLOBAL_STORY_NPC_PROGRESS = {}

# Stores NPC ID mappings for quick lookup per character.
# Format: { "char_id": { "npc_key": npc_id } }
STORY_NPC_ID_REGISTRY = {}

# Stores non-story NPC dialog runtime state per character.
# Format:
# {
#   "char_id": {
#       "npc_key": {
#           "remaining": ["line_a", "line_b", ...],
#           "last": "line_z",
#           "history": ["line_1", "line_2", ...]
#       }
#   }
# }
GLOBAL_REGULAR_NPC_STATE = {}

MAX_REGULAR_CHAT_HISTORY = 120

GENERIC_ROLE_CHAT_ALIASES = {
    "merchant": "merchant",
    "trainer": "trainer",
    "guard": "guard",
    "imperialguard": "imperialguard",
    "villager": "villager",
    "citizen": "citizen",
    "acolyte": "acolyte",
    "monk": "monk",
    "nomad": "nomad",
    "slave": "slave",
    # No dedicated "mayor" chat pool exists in data.npc_chats, so map to villager.
    "mayor": "villager",
}

ROLE_DIALOG_EXTENSIONS = {
    "villager": [
        "The roads feel calmer when heroes are nearby.",
        "We keep lanterns lit through the night.",
        "Food has gotten expensive this season.",
        "People sleep easier after patrols pass.",
        "Travelers say the old bridge creaks at dawn.",
        "A quiet morning is a rare blessing lately.",
        "The healer says rest is as important as steel.",
        "Everyone here knows someone who needs help.",
        "The weather turns quickly in these parts.",
        "A strong shield can save a whole party.",
    ],
    "merchant": [
        "I mark dangerous routes on my trade map.",
        "Good boots are worth every coin on long roads.",
        "Prices rise when caravans go missing.",
        "A repaired buckle can save an entire set of armor.",
        "Potion demand always spikes after stormy nights.",
        "I buy in bulk when escort guards are available.",
        "Steel and salt move faster than silk these days.",
        "Adventurers prefer supplies they can trust.",
        "Reliable ropes sell out before mountain runs.",
        "A smart buyer plans for the return trip too.",
    ],
    "trainer": [
        "Footwork first, power second.",
        "A clean block is better than a reckless swing.",
        "Recover your stance after every strike.",
        "Watch your timing, not just your target.",
        "Controlled breathing wins long fights.",
        "Training is repetition done with focus.",
        "Your guard should move before your fear does.",
        "Discipline is built between battles.",
        "Never waste motion when you can stay efficient.",
        "Learn the terrain before blades are drawn.",
    ],
    "guard": [
        "We rotate watch posts every few hours.",
        "Report unusual tracks as soon as you spot them.",
        "Night watch has been extended this week.",
        "Checkpoints stay active until sunrise.",
        "We escort families before we escort cargo.",
        "Suspicious movement gets logged immediately.",
        "Stay inside the marked routes after dark.",
        "Barricades hold better when people stay calm.",
        "Our patrol lines overlap for a reason.",
        "Keep your torch dry and your route simple.",
    ],
    "imperialguard": [
        "Imperial patrols are enforcing strict route checks.",
        "Orders are clear: protect civilians first.",
        "Discipline keeps this region standing.",
        "Keep your papers ready at major gates.",
        "Unauthorized movement is being tracked.",
        "We hold formation even under pressure.",
        "The Empire expects clean reports from every post.",
        "Security drills are mandatory this month.",
        "Supplies are protected by armed convoy.",
        "Alert commands will not be repeated twice.",
    ],
    "citizen": [
        "The market opens early when roads are safe.",
        "Families plan around the patrol bell now.",
        "Work never stops, but rumors travel faster.",
        "Most folks avoid side streets after sunset.",
        "People trade news while waiting in line.",
        "Repairs are happening all across town.",
        "Crowds gather quickly when guards pass by.",
        "Every district has its own worries these days.",
        "Nobody forgets the sound of last week's alarm.",
        "Routine keeps people steady.",
    ],
    "acolyte": [
        "Quiet prayer helps in uncertain times.",
        "We tend the wounded until dawn when needed.",
        "Light and patience carry many burdens.",
        "Take water and rest before your next mission.",
        "Mercy is strongest when it is practical.",
        "Keep hope alive through small acts.",
        "The shrine doors remain open to all travelers.",
        "Healing takes time and discipline.",
        "Peace begins with measured steps.",
        "Even warriors need stillness.",
    ],
    "monk": [
        "A calm mind sharpens every technique.",
        "Balance is trained, not gifted.",
        "Silence often reveals the safest path.",
        "Strength without control burns out quickly.",
        "Patience is a weapon too.",
        "Study your breath before your blade.",
        "Harmony in movement prevents mistakes.",
        "Awareness protects better than anger.",
        "Steady hands come from steady thoughts.",
        "A focused spirit endures longer.",
    ],
    "nomad": [
        "We move where water and safety allow.",
        "Campfires are small when the winds are loud.",
        "Routes shift with every season.",
        "Travel light and plan two exits.",
        "Tracks tell stories if you read them early.",
        "Sand and mud both hide danger well.",
        "Caravans survive by staying adaptable.",
        "A good scout is worth more than a fast horse.",
        "Never ignore a sudden silence on the road.",
        "Map the shade before you map the distance.",
    ],
    "slave": [
        "We keep working, one hour at a time.",
        "A kind word still matters in hard places.",
        "People survive by helping quietly.",
        "We notice who stands up for others.",
        "Even small relief can change a day.",
        "Some wounds are not visible right away.",
        "Hope is stubborn when shared.",
        "Strength is not always loud.",
        "Most people here just want safety.",
        "Respect costs nothing and means everything.",
    ],
    "default": [
        "Keep your gear ready before leaving town.",
        "Shortcuts are usually the most expensive path.",
        "Scouts say activity increases near dusk.",
        "A prepared group returns home.",
        "Most threats are easier to avoid than fight.",
        "The safest route is the one you can explain.",
        "Carry extra supplies for unexpected delays.",
        "Good information is worth more than rumors.",
        "Stay alert and travel with purpose.",
        "Every region has its own kind of trouble.",
    ],
}

# Additional mission-focused chatter injected for all mission-related NPCs.
QUEST_MISSION_DIALOG_EXTENSIONS = [
    "Check your mission tracker for the next objective.",
    "Report back after you complete the current task.",
    "Missions unlock routes, services, and useful contacts.",
    "If progress seems stuck, revisit your quest giver.",
    "Some tasks require talking to multiple NPCs in sequence.",
    "Mission updates help us keep the roads secure.",
    "Objectives can change after each completed step.",
    "If enemies feel too strong, finish pending missions first.",
    "Always verify whether you must return to complete the quest.",
    "Critical rewards are often tied to mission hand-ins.",
    "The mission board reflects your latest progress.",
    "A clear objective is better than a rushed detour.",
    "Coordinate with nearby NPCs before heading out.",
    "Completing missions keeps this region stable.",
    "Mission chains are easier when handled one step at a time.",
]

QUEST_MISSION_NAMED_DIALOG_TEMPLATES = [
    "{name} says your next objective is already in the tracker.",
    "{name} says this task is not complete until you report back.",
    "{name} says mission progress depends on the right sequence.",
    "{name} says you should finish current quests before taking new ones.",
    "{name} says the next mission contact is marked for you.",
    "{name} says they are waiting for your mission update.",
    "{name} says this region improves as mission work gets done.",
    "{name} says your best lead is the active quest objective.",
    "{name} says the board has new details after recent progress.",
    "{name} says returning to the quest giver is mandatory.",
]


# ── Mission runtime helpers (Newbie Road chain) ──

EARLY_STORY_MISSION_IDS = set(range(1, 9))  # DefendTheShip .. DeliverToSwamp


def _get_char_missions(char: dict) -> dict:
    missions = char.get("missions")
    if not isinstance(missions, dict):
        missions = {}
        char["missions"] = missions
    return missions


def _get_mission_state(char: dict, mission_id: int) -> int:
    missions = _get_char_missions(char)
    m = missions.get(str(mission_id)) or {}
    try:
        return int(m.get("state", Mission.const_213))
    except Exception:
        return Mission.const_213


def _set_mission_state(
    char: dict,
    mission_id: int,
    state: int,
    curr_count: int | None = None,
    tier: int | None = None,
    highscore: int | None = None,
    time_value: int | None = None,
) -> None:
    missions = _get_char_missions(char)
    m = missions.setdefault(str(mission_id), {})
    m["state"] = int(state)
    if curr_count is not None:
        m["currCount"] = int(curr_count)
    if tier is not None:
        m["Tier"] = int(tier)
    if highscore is not None:
        m["highscore"] = int(highscore)
    if time_value is not None:
        m["Time"] = int(time_value)


def _is_mission_completed(char: dict, mission_id: int) -> bool:
    return _get_mission_state(char, mission_id) == Mission.const_72


def _get_mission_prereq_ids(mission_id: int) -> list[int]:
    """
    Return prerequisite mission IDs for the given mission, based on
    MissionTypes.json's PreReqMissions field (comma/space separated names or IDs).
    """
    extra = get_mission_extra(mission_id) or {}
    raw = extra.get("PreReqMissions")
    if not raw:
        return []

    parts = str(raw).replace(";", ",").split(",")
    ids: list[int] = []
    for part in parts:
        token = part.strip()
        if not token:
            continue
        # Allow both numeric IDs and MissionName strings.
        try:
            mid = int(token)
            if mid > 0:
                ids.append(mid)
            continue
        except Exception:
            pass

        # Fallback: resolve by MissionName via a small one-shot scan of MissionTypes.json.
        # To avoid tight coupling with missions internals, look up by MissionName ad‑hoc.
        # This is only used for a tiny number of early-story missions.
        try:
            mission_file = os.path.join(os.path.dirname(__file__), "data", "MissionTypes.json")
            with open(mission_file, "r", encoding="utf-8") as f:
                rows = json.load(f)
        except Exception:
            continue

        token_lower = token.strip().lower()
        for row in rows:
            if not isinstance(row, dict):
                continue
            if str(row.get("MissionName", "")).strip().lower() == token_lower:
                try:
                    mid = int(row.get("MissionID", 0))
                except Exception:
                    mid = 0
                if mid > 0:
                    ids.append(mid)
                break

    # Deduplicate while preserving order
    seen = set()
    result = []
    for mid in ids:
        if mid not in seen:
            seen.add(mid)
            result.append(mid)
    return result


def _can_start_mission(char: dict, mission_id: int) -> bool:
    """
    Check whether all prerequisite missions (if any) are completed.
    Currently scoped to the early Newbie Road story chain (IDs 1–8).
    """
    if mission_id not in EARLY_STORY_MISSION_IDS:
        return True
    prereqs = _get_mission_prereq_ids(mission_id)
    if not prereqs:
        return True
    for mid in prereqs:
        if not _is_mission_completed(char, mid):
            return False
    return True


def _persist_char_missions(session, char: dict) -> None:
    """
    Persist mission changes for the active character back into the
    session.char_list and save to disk.
    """
    active_name = char.get("name")
    if not active_name:
        return
    for c in session.char_list:
        if c.get("name") == active_name:
            c.update(char)
            break
    session.current_char_dict = char
    if getattr(session, "user_id", None) is not None:
        save_characters(session.user_id, session.char_list)

def _build_mission_npc_keys():
    mission_file = os.path.join(os.path.dirname(__file__), "data", "MissionTypes.json")
    if not os.path.isfile(mission_file):
        return set()

    try:
        with open(mission_file, "r", encoding="utf-8") as f:
            rows = json.load(f)
    except Exception:
        return set()

    keys = set()
    for row in rows:
        if not isinstance(row, dict):
            continue

        for field_name in ("ContactName", "ReturnName"):
            raw_name = row.get(field_name)
            normalized = str(raw_name or "").replace(" ", "").replace("_", "").lower()
            if not normalized:
                continue

            keys.add(normalized)
            keys.add(re.sub(r"\d+$", "", normalized))

            if normalized.endswith("hard"):
                no_hard = normalized[:-4]
                keys.add(no_hard)
                keys.add(re.sub(r"\d+$", "", no_hard))

    keys.discard("")
    return keys

MISSION_NPC_KEYS = _build_mission_npc_keys()

def _build_level_interactable_index_maps():
    maps = {}
    if not os.path.isdir(WORLD_NPCS_DIR):
        return maps

    for filename in os.listdir(WORLD_NPCS_DIR):
        if not filename.lower().endswith(".json"):
            continue

        level_key = filename[:-5].strip().lower()
        json_path = os.path.join(WORLD_NPCS_DIR, filename)
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        level_map = {}
        for npc in data:
            if not isinstance(npc, dict):
                continue
            if int(npc.get("team", 0) or 0) != 3:
                continue

            character_name = (npc.get("character_name") or "").strip()
            if not character_name:
                continue

            npc_id = int(npc.get("id", 0) or 0)
            if npc_id <= 0:
                continue

            idx = npc_id >> 16
            normalized_name = character_name.replace(" ", "").replace("_", "").lower()
            if normalized_name:
                level_map[idx] = normalized_name

        if level_map:
            maps[level_key] = level_map

    return maps

LEVEL_INTERACTABLE_INDEX_MAPS = _build_level_interactable_index_maps()

def _ensure_story_npc_state(char_id):
    """Initialize per-character Story NPC state containers if missing."""
    if char_id not in GLOBAL_STORY_NPC_HISTORY:
        GLOBAL_STORY_NPC_HISTORY[char_id] = {}
    if char_id not in GLOBAL_STORY_NPC_PROGRESS:
        GLOBAL_STORY_NPC_PROGRESS[char_id] = {}
    if char_id not in STORY_NPC_ID_REGISTRY:
        STORY_NPC_ID_REGISTRY[char_id] = {}

def _get_story_npc_lines(npc_key):
    # Keep the 4 SwampRoadNorth Halloween statues fully isolated from NPC_CHATS edits.
    if npc_key in LOCKED_HALLOWEEN_STATUE_DIALOGS:
        return list(LOCKED_HALLOWEEN_STATUE_DIALOGS[npc_key])
    return NPC_CHATS.get(npc_key, ["..."])

def _send_story_npc_dialog(session, npc_id, npc_key, source_tag):
    """
    Send the next Story NPC line without depending on clientEntID.
    Once all lines are consumed, do not repeat.
    """
    char_id = session.current_character or "unknown"
    _ensure_story_npc_state(char_id)
    level_name = getattr(session, "current_level", None)

    STORY_NPC_ID_REGISTRY[char_id][npc_key] = npc_id
    if _is_story_npc_level(level_name):
        _cache_story_statue_id(session, level_name, npc_id, npc_key)
        client_ent_id = getattr(session, "clientEntID", None)
        if isinstance(client_ent_id, int) and client_ent_id > 0:
            _cache_story_player_idx(session, level_name, client_ent_id >> 16)

    all_lines = _get_story_npc_lines(npc_key)
    next_index = GLOBAL_STORY_NPC_PROGRESS[char_id].get(npc_key, 0)

    if next_index >= len(all_lines):
        print(
            f"[{session.addr}] [PKT0x7A] STORY NPC ({source_tag}) {npc_key}: "
            f"dialog exhausted, skipping repeat (Character: {char_id})"
        )
        return

    text = all_lines[next_index]
    GLOBAL_STORY_NPC_PROGRESS[char_id][npc_key] = next_index + 1

    seen = GLOBAL_STORY_NPC_HISTORY[char_id].get(npc_key, [])
    if text not in seen:
        seen.append(text)
    GLOBAL_STORY_NPC_HISTORY[char_id][npc_key] = seen

    if not hasattr(session, "_npc_chat_history"):
        session._npc_chat_history = {}
    session._npc_chat_history[npc_key] = list(seen)

    send_npc_dialog(session, npc_id, text)
    print(
        f"[{session.addr}] [PKT0x7A] STORY NPC ({source_tag}) {npc_key}: \"{text}\" "
        f"(Character: {char_id}, Line {next_index + 1}/{len(all_lines)})"
    )

def _ensure_regular_npc_state(char_id):
    if char_id not in GLOBAL_REGULAR_NPC_STATE:
        GLOBAL_REGULAR_NPC_STATE[char_id] = {}

def _norm_npc_key(value):
    return (value or "").replace(" ", "").replace("_", "").lower()

def _canonical_story_npc_key(value):
    key = _norm_npc_key(value)
    if key in STORY_NPCS:
        return key
    return STORY_NPC_ALIASES.get(key)

def _norm_identity_name(value):
    return re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())

def _mark_max_hp_sync(session):
    session.max_hp_sync_level = getattr(session, "current_level", None)
    session.max_hp_sync_ts = time.time()

def _has_max_hp_sync_for_current_level(session):
    current_level = getattr(session, "current_level", None)
    synced_level = getattr(session, "max_hp_sync_level", None)
    return bool(current_level and synced_level == current_level)

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

def _request_client_hp_report(session, reason=0):
    if not session or not getattr(session, "conn", None):
        return
    bb = BitBuffer()
    bb.write_method_6(int(reason), Game.const_390)
    payload = bb.to_bytes()
    packet = struct.pack(">HH", 0xF9, len(payload)) + payload
    try:
        session.conn.sendall(packet)
    except OSError:
        return

def _resolve_active_player_entity_id(session):
    entities = getattr(session, "entities", None)
    current_name_norm = _norm_identity_name(getattr(session, "current_character", None))
    client_ent_id = getattr(session, "clientEntID", None)

    if isinstance(client_ent_id, int) and client_ent_id > 0 and isinstance(entities, dict):
        ent = entities.get(client_ent_id)
        if isinstance(ent, dict):
            ent_name_norm = _norm_identity_name(ent.get("ent_name") or ent.get("name"))
            if not current_name_norm or ent_name_norm == current_name_norm:
                return client_ent_id

    if isinstance(entities, dict):
        for eid, ent in entities.items():
            if not isinstance(eid, int) or not isinstance(ent, dict):
                continue
            if not ent.get("is_player"):
                continue
            ent_name_norm = _norm_identity_name(ent.get("ent_name") or ent.get("name"))
            if current_name_norm and ent_name_norm != current_name_norm:
                continue
            session.clientEntID = eid
            return eid

    return client_ent_id if isinstance(client_ent_id, int) and client_ent_id > 0 else None

def _resolve_authoritative_hp_state(session):
    ent = None
    client_ent_id = _resolve_active_player_entity_id(session)
    if client_ent_id is not None:
        ent = session.entities.get(client_ent_id)
        if not isinstance(ent, dict):
            ent = None

    max_hp = getattr(session, "authoritative_max_hp", None)
    if max_hp is None and ent is not None:
        max_hp = ent.get("max_hp", None)
    max_hp = int(max_hp) if max_hp is not None else 100
    if max_hp <= 0:
        max_hp = 100

    current_hp = getattr(session, "authoritative_current_hp", None)
    if current_hp is None:
        if ent is not None and "hp" in ent:
            current_hp = int(ent.get("hp", max_hp))
        else:
            current_hp = max_hp
    current_hp = min(max(0, int(current_hp)), max_hp)
    return max_hp, current_hp, ent

def _send_player_hp_update(session, delta):
    try:
        amount = int(delta)
    except Exception:
        return False
    if amount == 0:
        return False

    entity_id = _resolve_active_player_entity_id(session)
    if entity_id is None:
        print(f"[HP Sync] Failed to resolve active player entity for HP update delta={amount}.")
        return False

    if amount > 0:
        # 0x3B drives the same HP update path but shows local green heal floater text.
        send_entity_heal(session, entity_id, amount)
    else:
        send_hp_update(session, entity_id, amount)
    session.last_server_hp_adjust_ts = time.time()
    session.last_server_hp_adjust_delta = amount
    return True

def _get_recent_client_hp(session, max_age_sec=2.5):
    try:
        reported_hp = int(getattr(session, "last_client_hp_report_value", -1))
    except Exception:
        return None
    if reported_hp < 0:
        return None

    ts = getattr(session, "last_client_hp_report_ts", None)
    try:
        report_ts = float(ts)
        age = time.time() - report_ts
    except Exception:
        return None
    if age < 0 or age > float(max_age_sec):
        return None

    # Ignore client reports older than the last server-side HP delta packet;
    # using them can double-apply orb heals.
    try:
        last_adjust_ts = float(getattr(session, "last_server_hp_adjust_ts", 0.0) or 0.0)
    except Exception:
        last_adjust_ts = 0.0
    if report_ts <= (last_adjust_ts + 0.005):
        return None

    return reported_hp

def _schedule_pending_orb_hp_report_retries(session, pending_token):
    def _worker():
        # Client can throttle consecutive 0xF9-triggered reports for a short window.
        # Retry a few times while this pending orb is still active.
        for delay in (0.35, 0.90, 1.80):
            time.sleep(delay)
            if not getattr(session, "running", False):
                return
            pending = getattr(session, "pending_orb_heal", None)
            if not isinstance(pending, dict) or pending.get("token") != pending_token:
                return
            expires_at = float(pending.get("expires_at", 0.0) or 0.0)
            if time.time() > expires_at:
                return
            _request_client_hp_report(session, reason=1)

    threading.Thread(target=_worker, daemon=True).start()

def _queue_pending_orb_heal(session, amount, *, wait_for_max_sync=False, picked_at_full=False):
    now = time.time()
    current_level = getattr(session, "current_level", None)
    existing = getattr(session, "pending_orb_heal", None)
    created_new = False

    if (
        isinstance(existing, dict)
        and existing.get("level") == current_level
        and now <= float(existing.get("expires_at", 0.0) or 0.0)
    ):
        entries = existing.setdefault("entries", [])
        entries.append({
            "amount": int(amount),
            "queued_at": now,
            "picked_at_full": bool(picked_at_full),
        })
        existing["amount"] = int(existing.get("amount", 0) or 0) + int(amount)
        existing["picked_at_full"] = bool(existing.get("picked_at_full", False) or picked_at_full)
        existing["wait_for_max_sync"] = bool(existing.get("wait_for_max_sync", False) or wait_for_max_sync)
        existing["expires_at"] = now + 6.0
        pending_token = int(existing.get("token", 0) or 0)
    else:
        created_new = True
        pending_token = int(time.time_ns() & 0x7FFFFFFF)
        session.pending_orb_heal = {
            "token": pending_token,
            "entries": [{
                "amount": int(amount),
                "queued_at": now,
                "picked_at_full": bool(picked_at_full),
            }],
            "amount": int(amount),
            "queued_at": now,
            "expires_at": now + 6.0,
            "wait_for_max_sync": bool(wait_for_max_sync),
            "picked_at_full": bool(picked_at_full),
            "level": current_level,
        }

    if wait_for_max_sync:
        _request_client_combat_stats_sync(session)
    _request_client_hp_report(session)
    if created_new:
        _schedule_pending_orb_hp_report_retries(session, pending_token)

def _level_cache_key(level_name):
    return (level_name or "").strip().lower()

def _ensure_story_level_cache(session, attr_name):
    cache = getattr(session, attr_name, None)
    if not isinstance(cache, dict):
        cache = {}
        setattr(session, attr_name, cache)
    return cache

def _cache_story_player_idx(session, level_name, player_idx):
    try:
        idx = int(player_idx)
    except Exception:
        return
    cache = _ensure_story_level_cache(session, "_story_player_idx_by_level")
    cache[_level_cache_key(level_name)] = idx

def _get_cached_story_player_idx(session, level_name):
    cache = _ensure_story_level_cache(session, "_story_player_idx_by_level")
    value = cache.get(_level_cache_key(level_name))
    try:
        return int(value) if value is not None else None
    except Exception:
        return None

def _cache_story_statue_id(session, level_name, npc_id, story_key):
    if story_key not in STORY_NPCS:
        return
    try:
        nid = int(npc_id)
    except Exception:
        return
    top = _ensure_story_level_cache(session, "_story_statue_id_cache")
    lvl = top.setdefault(_level_cache_key(level_name), {})
    if not isinstance(lvl, dict):
        lvl = {}
        top[_level_cache_key(level_name)] = lvl
    lvl[nid] = story_key

def _get_cached_story_statue_key(session, level_name, npc_id):
    try:
        nid = int(npc_id)
    except Exception:
        return None
    top = _ensure_story_level_cache(session, "_story_statue_id_cache")
    lvl = top.get(_level_cache_key(level_name))
    if not isinstance(lvl, dict):
        return None
    story_key = lvl.get(nid)
    return story_key if story_key in STORY_NPCS else None

def _get_story_statue_relative_indices(level_name):
    if not _is_story_npc_level(level_name):
        return {}
    return STORY_STATUE_RELATIVE_INDICES

def _resolve_active_client_ent_id(session, level_name):
    if not _is_story_npc_level(level_name):
        return None

    current_name_norm = _norm_identity_name(getattr(session, "current_character", None))
    known_eid = getattr(session, "clientEntID", None)
    entities = getattr(session, "entities", {})

    if isinstance(known_eid, int) and known_eid > 0 and isinstance(entities, dict):
        ent = entities.get(known_eid)
        if isinstance(ent, dict) and ent.get("is_player"):
            ent_name = ent.get("ent_name") or ent.get("name")
            if not current_name_norm or _norm_identity_name(ent_name) == current_name_norm:
                _cache_story_player_idx(session, level_name, known_eid >> 16)
                return known_eid

    if not isinstance(entities, dict):
        return None

    for entity_id, ent in entities.items():
        if not isinstance(ent, dict):
            continue
        if not ent.get("is_player"):
            continue
        ent_name = ent.get("ent_name") or ent.get("name")
        if current_name_norm and _norm_identity_name(ent_name) != current_name_norm:
            continue
        try:
            eid = int(entity_id)
        except Exception:
            continue
        _cache_story_player_idx(session, level_name, eid >> 16)
        return eid

    return None

def _select_story_candidate(candidates):
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], STORY_STATUE_TIEBREAK.get(item[1], 99)))
    return candidates[0]

def _resolve_story_key_by_relative_idx(npc_id, client_ent_id, level_name, tolerance=1):
    story_indices = _get_story_statue_relative_indices(level_name)
    if not story_indices:
        return None, None

    try:
        relative_idx = (int(npc_id) - int(client_ent_id)) >> 16
    except Exception:
        return None, None

    candidates = []
    for idx, story_key in story_indices.items():
        delta = abs(relative_idx - idx)
        if delta <= tolerance:
            candidates.append((delta, story_key, idx))

    selected = _select_story_candidate(candidates)
    if not selected:
        return None, relative_idx

    _, story_key, matched_idx = selected
    return story_key, matched_idx

def _resolve_story_key_by_player_idx(npc_id, player_idx, level_name, tolerance=1):
    story_indices = _get_story_statue_relative_indices(level_name)
    if not story_indices:
        return None, None

    try:
        relative_idx = (int(npc_id) >> 16) - int(player_idx)
    except Exception:
        return None, None

    candidates = []
    for idx, story_key in story_indices.items():
        delta = abs(relative_idx - idx)
        if delta <= tolerance:
            candidates.append((delta, story_key, idx))

    selected = _select_story_candidate(candidates)
    if not selected:
        return None, relative_idx

    _, story_key, matched_idx = selected
    return story_key, matched_idx

def _guess_story_key_nearest(npc_id, level_name, baseline_player_idx=None):
    story_indices = _get_story_statue_relative_indices(level_name)
    if not story_indices:
        return None, None

    npc_abs_idx = int(npc_id) >> 16
    if baseline_player_idx is None:
        # Deterministic default keeps guesses stable when no player index is available.
        baseline_player_idx = npc_abs_idx - 32

    candidates = []
    for rel_idx, story_key in story_indices.items():
        score = abs((npc_abs_idx - rel_idx) - baseline_player_idx)
        candidates.append((score, story_key, rel_idx))

    selected = _select_story_candidate(candidates)
    if not selected:
        return None, baseline_player_idx

    _, story_key, _ = selected
    return story_key, baseline_player_idx

def _resolve_locked_story_npc_key(session, npc_id, level_name, npc=None, client_ent_id=None):
    if not _is_story_npc_level(level_name):
        return None, None

    # Try direct identity fields first.
    candidate_names = []

    def add_candidate(value):
        normalized = _norm_npc_key(value)
        if normalized and normalized not in candidate_names:
            candidate_names.append(normalized)

    if isinstance(npc, dict):
        add_candidate(npc.get("character_name"))
        cue_data = npc.get("cue_data") or {}
        if isinstance(cue_data, dict):
            add_candidate(cue_data.get("character_name"))
        add_candidate(npc.get("entType"))
        add_candidate(npc.get("name"))

    for source in candidate_names:
        for candidate in _derive_npc_lookup_keys(source):
            canonical = _canonical_story_npc_key(candidate)
            if canonical:
                _cache_story_statue_id(session, level_name, npc_id, canonical)
                return canonical, "LOCKED-IDENTITY"

    # If we already have a specific non-statue identity, do not force index fallback.
    # This avoids accidental statue resolution for nearby non-story NPC indices.
    if candidate_names and not any("halloweenstatue" in name for name in candidate_names):
        return None, None

    # Stage 2: runtime cache (npc_id -> story_key) for this level.
    cached_story_key = _get_cached_story_statue_key(session, level_name, npc_id)
    if cached_story_key:
        return cached_story_key, "LOCKED-INDEX"

    # Stage 3: resolve using active (validated) clientEntID.
    active_client_ent_id = _resolve_active_client_ent_id(session, level_name)
    if active_client_ent_id is not None:
        story_key, _ = _resolve_story_key_by_relative_idx(
            npc_id,
            active_client_ent_id,
            level_name,
            tolerance=1,
        )
        if story_key:
            _cache_story_player_idx(session, level_name, active_client_ent_id >> 16)
            _cache_story_statue_id(session, level_name, npc_id, story_key)
            return story_key, "LOCKED-INDEX"

    # Stage 4: resolve from cached player index for the same level.
    cached_player_idx = _get_cached_story_player_idx(session, level_name)
    if cached_player_idx is not None:
        story_key, _ = _resolve_story_key_by_player_idx(
            npc_id,
            cached_player_idx,
            level_name,
            tolerance=1,
        )
        if story_key:
            _cache_story_statue_id(session, level_name, npc_id, story_key)
            return story_key, "LOCKED-INDEX"

    # Stage 5: nearest deterministic guess (never generic for these statues).
    baseline_player_idx = None
    if active_client_ent_id is not None:
        baseline_player_idx = active_client_ent_id >> 16
    elif cached_player_idx is not None:
        baseline_player_idx = cached_player_idx
    elif isinstance(client_ent_id, int) and client_ent_id > 0:
        baseline_player_idx = client_ent_id >> 16

    guessed_story_key, guessed_player_idx = _guess_story_key_nearest(
        npc_id,
        level_name,
        baseline_player_idx=baseline_player_idx,
    )
    if guessed_story_key:
        if guessed_player_idx is not None:
            _cache_story_player_idx(session, level_name, guessed_player_idx)
        _cache_story_statue_id(session, level_name, npc_id, guessed_story_key)
        return guessed_story_key, "LOCKED-GUESS"

    return None, None

def _derive_npc_lookup_keys(npc_type_norm):
    keys = []

    def add(k):
        if k and k not in keys:
            keys.append(k)

    add(npc_type_norm)
    add(re.sub(r"\d+$", "", npc_type_norm))

    for key in list(keys):
        if key.endswith("hard"):
            no_hard = key[:-4]
            add(no_hard)
            add(re.sub(r"\d+$", "", no_hard))

    return keys

def _humanize_npc_display_name(raw_name):
    text = (raw_name or "").strip()
    if not text:
        return "Traveler"

    text = re.sub(r"hard$", "", text, flags=re.IGNORECASE)
    text = text.replace("_", " ")
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    text = re.sub(r"\d+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or "Traveler"

def _guess_generic_npc_chat_key(npc_key):
    normalized = _norm_npc_key(npc_key)
    for token, chat_key in GENERIC_ROLE_CHAT_ALIASES.items():
        if token in normalized:
            return chat_key
    return "villager"

def _resolve_regular_npc_chat_key(raw_name, npc_id=None):
    lookup_keys = _derive_npc_lookup_keys(_norm_npc_key(raw_name))

    for key in lookup_keys:
        if key in NPC_CHATS:
            return key

    guessed = _guess_generic_npc_chat_key(lookup_keys[0] if lookup_keys else raw_name)
    if guessed in NPC_CHATS:
        return guessed

    if lookup_keys:
        return lookup_keys[0]

    if npc_id is not None:
        return f"unknownnpc{npc_id}"
    return "unknownnpc"

def _is_mission_npc(npc_key, raw_name=None):
    candidate_sources = [npc_key, raw_name]
    for source in candidate_sources:
        normalized = _norm_npc_key(source)
        if not normalized:
            continue

        for candidate in _derive_npc_lookup_keys(normalized):
            if candidate not in MISSION_NPC_KEYS:
                continue
            # Preserve special 4-player Story NPC flow exactly as-is.
            if _canonical_story_npc_key(candidate):
                continue
            return True
    return False

def _get_role_dialog_extensions(npc_key, raw_name=None):
    role_key = npc_key if npc_key in ROLE_DIALOG_EXTENSIONS else _guess_generic_npc_chat_key(raw_name or npc_key)
    merged = []
    for source_key in (role_key, "default"):
        for line in ROLE_DIALOG_EXTENSIONS.get(source_key, []):
            if line and line not in merged:
                merged.append(line)
    return merged

def _get_mission_dialog_extensions(npc_key, raw_name=None):
    if not _is_mission_npc(npc_key, raw_name):
        return []

    merged = []
    for line in QUEST_MISSION_DIALOG_EXTENSIONS:
        if line and line not in merged:
            merged.append(line)

    display = _humanize_npc_display_name(raw_name or npc_key)
    for template in QUEST_MISSION_NAMED_DIALOG_TEMPLATES:
        line = template.format(name=display)
        if line and line not in merged:
            merged.append(line)

    return merged

def _build_npc_dialog_pool(npc_key, raw_name=None):
    explicit_lines = NPC_CHATS.get(npc_key, [])
    merged = []
    for line in explicit_lines:
        if line and line not in merged:
            merged.append(line)

    if not merged:
        fallback_key = _guess_generic_npc_chat_key(raw_name or npc_key)
        fallback_lines = NPC_CHATS.get(fallback_key, [])
        for line in fallback_lines:
            if line and line not in merged:
                merged.append(line)

    for line in _get_role_dialog_extensions(npc_key, raw_name):
        if line and line not in merged:
            merged.append(line)

    for line in _get_mission_dialog_extensions(npc_key, raw_name):
        if line and line not in merged:
            merged.append(line)

    if not merged:
        display = _humanize_npc_display_name(raw_name or npc_key)
        merged.append(f"{display} nods in silence.")

    return merged

def _build_non_repeating_cycle(all_lines, last_line=None):
    unique_lines = []
    for line in all_lines:
        if line and line not in unique_lines:
            unique_lines.append(line)

    if len(unique_lines) <= 1:
        return unique_lines

    cycle = list(unique_lines)
    random.shuffle(cycle)

    if last_line and cycle[0] == last_line:
        for i in range(1, len(cycle)):
            if cycle[i] != last_line:
                cycle[0], cycle[i] = cycle[i], cycle[0]
                break

    return cycle

def _send_regular_npc_dialog(session, npc_id, npc_key, all_lines, source_tag, raw_name=None):
    char_id = session.current_character or "unknown"
    _ensure_regular_npc_state(char_id)

    char_state = GLOBAL_REGULAR_NPC_STATE[char_id]
    npc_state = char_state.get(npc_key, {"remaining": [], "last": None, "history": []})

    remaining = list(npc_state.get("remaining", []))
    last_line = npc_state.get("last")
    if not remaining:
        remaining = _build_non_repeating_cycle(all_lines, last_line=last_line)
        if not remaining:
            print(
                f"[{session.addr}] [PKT0x7A] NPC ({source_tag}) {npc_key}: "
                f"no dialog lines available (Character: {char_id})"
            )
            return False

    text = remaining.pop(0)
    history = list(npc_state.get("history", []))
    history.append(text)
    if len(history) > MAX_REGULAR_CHAT_HISTORY:
        history = history[-MAX_REGULAR_CHAT_HISTORY:]

    npc_state["remaining"] = remaining
    npc_state["last"] = text
    npc_state["history"] = history
    char_state[npc_key] = npc_state

    if not hasattr(session, "_npc_chat_history"):
        session._npc_chat_history = {}
    session._npc_chat_history[npc_key] = list(history)

    send_npc_dialog(session, npc_id, text)
    print(
        f"[{session.addr}] [PKT0x7A] NPC ({source_tag}) {npc_key}: \"{text}\" "
        f"(Character: {char_id}, Seen={len(history)}, RemainingCycle={len(remaining)})"
    )
    return True

def _is_story_npc_level(level_name):
    return (level_name or "").strip().lower().startswith(STORY_NPC_LEVEL_PREFIX)

def _get_level_index_map(level_name):
    normalized = (level_name or "").strip().lower()
    if not normalized:
        return None

    exact = LEVEL_INTERACTABLE_INDEX_MAPS.get(normalized)

    # HARDCODED OVERRIDES FOR CLIENT SWF ENTITY INDICES
    # The client SWF has Captain Fink at index 29 in NewbieRoad (ID 1919371)
    if normalized == "newbieroad":
        if exact is None:
            exact = {}
        exact[29] = "captainfink"

    if exact:
        return exact

    if normalized.endswith("hard"):
        return LEVEL_INTERACTABLE_INDEX_MAPS.get(normalized[:-4])

    return None

def _resolve_index_mapped_npc_name(npc_id, level_name, client_ent_id=None, story_only=False):
    level_map = _get_level_index_map(level_name)
    if not level_map:
        return None, -1

    min_known_idx = min(level_map)
    max_known_idx = max(level_map)

    base_candidates = []
    absolute_idx = npc_id >> 16
    base_candidates.append(absolute_idx)

    if client_ent_id is not None:
        try:
            client_idx = int(client_ent_id) >> 16
            relative_idx = absolute_idx - client_idx
            if relative_idx not in base_candidates:
                base_candidates.insert(0, relative_idx)
        except Exception:
            pass

    seen_indices = set()

    for base_idx in base_candidates:
        for delta in (0, -1, 1):
            start_idx = base_idx + delta

            idx = start_idx
            while idx >= min_known_idx:
                if idx not in seen_indices:
                    seen_indices.add(idx)
                    name = level_map.get(idx)
                    if name:
                        if story_only:
                            story_key = _canonical_story_npc_key(name)
                            if story_key:
                                return story_key, idx
                        else:
                            return name, idx
                idx -= 186

            idx = start_idx + 186
            while idx <= max_known_idx:
                if idx not in seen_indices:
                    seen_indices.add(idx)
                    name = level_map.get(idx)
                    if name:
                        if story_only:
                            story_key = _canonical_story_npc_key(name)
                            if story_key:
                                return story_key, idx
                        else:
                            return name, idx
                idx += 186

    return None, -1

def handle_dungeon_run_report(session, data):
    br = BitReader(data[4:])

    master_class_id           = br.read_method_20(Game.const_209)
    player_level              = br.read_method_9()
    session_play_time         = br.read_method_9()
    time_in_combat            = br.read_method_9()
    total_damage_dealt_player = br.read_method_24()
    total_damage_dealt_pets   = br.read_method_24()
    expected_damage_scale     = br.read_method_24()
    kills                     = br.read_method_24()
    healing_dealt             = br.read_method_24()
    damage_received           = br.read_method_24()
    damage_resisted           = br.read_method_24()
    deaths                    = br.read_method_24()
    healing_received          = br.read_method_24()
    primary_damage_stat       = br.read_method_24()
    magic_damage              = br.read_method_24()
    armor_class               = br.read_method_24()
    attack_speed_scaled       = br.read_method_24()
    movement_speed_scaled     = br.read_method_24()
    max_hp                    = br.read_method_24()
    average_group_size_scaled = br.read_method_24()
    session_flags_bitfield    = br.read_method_20(class_119.const_228)
    time_rank                 = br.read_method_9()
    kills_score               = br.read_method_9()
    accuracy_score            = br.read_method_9()
    deaths_score              = br.read_method_9()
    treasure_score            = br.read_method_9()
    time_score                = br.read_method_9()
    entries = []
    while br.read_method_15():
        entry = read_class_166(br)
        entries.append(entry)

    log_block = {
    "master_class_id"           : master_class_id,
    "player_level"              : player_level,
    "session_play_time"         : session_play_time,
    "time_in_combat"            : time_in_combat,
    "total_damage_dealt_player" : total_damage_dealt_player,
    "total_damage_dealt_pets"   : total_damage_dealt_pets,
    "expected_damage_scale"     : expected_damage_scale,
    "kills"                     : kills,
    "healing_dealt"             : healing_dealt,
    "damage_received"           : damage_received,
    "damage_resisted"           : damage_resisted,
    "deaths"                    : deaths,
    "healing_received"          : healing_received,
    "primary_damage_stat"       : primary_damage_stat,
    "magic_damage"              : magic_damage,
    "armor_class"               : armor_class,
    "attack_speed_scaled"       : attack_speed_scaled,
    "movement_speed_scaled"     : movement_speed_scaled,
    "max_hp"                    : max_hp,
    "average_group_size_scaled" : average_group_size_scaled,
    "session_flags_bitfield"    : session_flags_bitfield,
    "time_rank"                 : time_rank,
    "kills_score"               : kills_score,
    "accuracy_score"            : accuracy_score,
    "deaths_score"              : deaths_score,
    "treasure_score"            : treasure_score,
    "time_score"                : time_score,
    }
    #pprint(log_block)
    #print(f"power_stats_count = {len(entries)}")

def read_class_166(br):
    entry = {}

    entry["stat_id"] = br.read_method_9()
    entry["delta"]   = br.read_method_24()
    entry["time"]    = br.read_method_24()

    return entry

#TODO...
#these names may be wrong
def handle_set_level_complete(session, data):
    br = BitReader(data[4:])

    pkt_completion_percent = br.read_method_9()
    pkt_bonus_score_total  = br.read_method_9()
    pkt_gold_reward        = br.read_method_9()
    pkt_material_reward    = br.read_method_9()
    pkt_gear_count         = br.read_method_9()
    pkt_remaining_kills    = br.read_method_9()
    pkt_required_kills     = br.read_method_9()
    pkt_level_width_score  = br.read_method_9()

    # Calculate actual kills using authoritative server dungeon tracker when available
    run = GS.dungeon_runs.get(session.current_level)
    if run:
        actual_kills = run.get("killed", 0)
    else:
        # Fallback to client-reported values
        actual_kills = pkt_required_kills - pkt_remaining_kills

    # Check for any active mission that relies on this dungeon to complete
    char = session.current_char_dict or {}
    player_missions = char.get("missions", {})
    from globals import send_mission_complete
    
    completed_mission_id = None
    for mid_str, mdata in player_missions.items():
        if mdata.get("state") == Mission.const_58:  # In progress
            try:
                mid = int(mid_str)
            except:
                continue
            
            # Use get_mission_def to check if this mission's Dungeon matches
            from missions import get_mission_def
            mdef = get_mission_def(mid)
            if mdef.get("Dungeon") == session.current_level:
                # Complete the dungeon mission
                _set_mission_state(char, mid, Mission.const_72)
                _persist_char_missions(session, char)
                completed_mission_id = mid
                send_mission_complete(session, mid)
                break

    if completed_mission_id is not None:
        # Send 0x84 (Mission Complete UI) for the dungeon mission
        bb = BitBuffer()
        bb.write_method_4(completed_mission_id)
        bb.write_method_11(True) # true if this is a dungeon
        bb.write_method_6(pkt_level_width_score or 3, 4) # Stars
        bb.write_method_4(pkt_bonus_score_total) # Dungeon score
        payload = bb.to_bytes()
        session.conn.sendall(struct.pack(">HH", 0x84, len(payload)) + payload)
    
    # Always send dungeon completion with actual values from client
    send_dummy_level_complete(
        session,
        kills=actual_kills,
        treasure=pkt_gold_reward,
    )

def send_dummy_level_complete(
    session,
    stars=3,
    result_bar=1,
    rank=1,
    kills=50,
    accuracy=50,
    deaths=5,
    treasure=5000,
    time=6000,
):
    bb = BitBuffer()

    bb.write_method_6(stars, 4)
    bb.write_method_4(result_bar)
    bb.write_method_4(rank)
    bb.write_method_4(kills)
    bb.write_method_4(accuracy)
    bb.write_method_4(deaths)
    bb.write_method_4(treasure)
    bb.write_method_4(time)

    payload = bb.to_bytes()
    pkt = struct.pack(">HH", 0x87, len(payload)) + payload
    session.conn.sendall(pkt)


def handle_send_combat_stats(session, data):
    br = BitReader(data[4:])

    melee_damage = br.read_method_9()
    magic_damage = br.read_method_9()
    max_hp       = br.read_method_9()

    stat_scale   = br.read_method_20(Game.const_794)
    stat_rev     = br.read_method_9()
    print(
        f"[COMBAT_STATS] melee={melee_damage} "
        f"magic={magic_damage} "
        f"maxHP={max_hp} "
        f"scale={stat_scale} "
        f"rev={stat_rev}"
    )

    # Sync with player entity
    ent = session.entities.get(session.clientEntID)
    session.authoritative_max_hp = max_hp # Store on session for persistence across level loads
    _mark_max_hp_sync(session)

    print(f"[HP Sync] Stats from client: melee={melee_damage}, magic={magic_damage}, max_hp={max_hp}, rev={stat_rev}")
    
    if ent:
        prev_max_hp = ent.get("max_hp", 0)
        ent["max_hp"] = max_hp
        
        # If this is the first time we get stats or max_hp increased, 
        # initialize hp if not already set or at old max
        if "hp" not in ent or ent["hp"] == prev_max_hp:
            ent["hp"] = max_hp
        else:
            # Ensure current HP doesn't exceed new max
            ent["hp"] = min(ent["hp"], max_hp)

        session.authoritative_current_hp = int(ent.get("hp", max_hp))
    else:
        prev_hp = getattr(session, "authoritative_current_hp", None)
        if prev_hp is None:
            session.authoritative_current_hp = max_hp
        else:
            session.authoritative_current_hp = min(max(0, int(prev_hp)), max_hp)

    pending_orb_heal = getattr(session, "pending_orb_heal", None)
    if pending_orb_heal:
        _request_client_hp_report(session, reason=2)


#TODO...
def handle_pickup_lootdrop(session, data):
    br = BitReader(data[4:])
    loot_id = br.read_method_9()

    # Check if we have record of this loot
    loot = getattr(session, "pending_loot", {}).pop(loot_id, None)
    
    if loot:
        char = session.current_char_dict
        if not char: return

        save_needed = False

        if "gold" in loot:
            amount = int(loot.get("gold", 0))
            current_gold = int(char.get("gold", 0))
            char["gold"] = current_gold + amount
            # Use visible pickup mode to ensure the client applies the increment immediately.
            send_gold_reward(session, amount, suppress=False)
            save_needed = True
            print(f"[Loot] {char['name']} picked up {amount} Gold. Total now {char['gold']}.")

        if "health" in loot:
            hp_gain = int(loot["health"])
            max_hp, current_hp, ent = _resolve_authoritative_hp_state(session)
            session.authoritative_current_hp = current_hp
            
            if ent:
                ent["max_hp"] = max_hp  # Keep entity in sync
                ent["hp"] = current_hp
                
            # Check if already at max HP
            actual_gain = 0
            hp_sync_ready = _has_max_hp_sync_for_current_level(session)
            if not hp_sync_ready:
                picked_at_full = current_hp >= max_hp
                _queue_pending_orb_heal(
                    session,
                    hp_gain,
                    wait_for_max_sync=True,
                    picked_at_full=picked_at_full,
                )
                print(
                    f"[Loot] {char['name']} deferred orb heal +{hp_gain}; "
                    f"waiting for max HP sync in {session.current_level}."
                )
            elif current_hp >= max_hp:
                recent_client_hp = _get_recent_client_hp(session, max_age_sec=2.5)
                if recent_client_hp is not None and recent_client_hp < max_hp:
                    reconciled_hp = min(max_hp, max(0, int(recent_client_hp)))
                    apply_gain = min(max_hp - reconciled_hp, hp_gain)
                    if apply_gain > 0:
                        new_hp = reconciled_hp + apply_gain
                        session.authoritative_current_hp = new_hp
                        if ent:
                            ent["hp"] = new_hp
                        _send_player_hp_update(session, apply_gain)
                        actual_gain = apply_gain
                        print(
                            f"[HP DriftFix] Used recent client HP report ({reconciled_hp}/{max_hp}) "
                            f"for immediate orb heal +{apply_gain}."
                        )
                    else:
                        print(
                            f"[Loot] {char['name']} orb ignored after report reconcile "
                            f"(report={reconciled_hp}/{max_hp})."
                        )
                else:
                    print(f"[Loot] {char['name']} picked up health globe but HP is full (HP: {current_hp}/{max_hp}).")

                    # Fallback path only when recent report is unavailable.
                    _queue_pending_orb_heal(
                        session,
                        hp_gain,
                        wait_for_max_sync=False,
                        picked_at_full=True,
                    )
            else:
                # Always clamp to max HP
                new_hp = min(max_hp, current_hp + hp_gain)
                actual_gain = new_hp - current_hp
                session.authoritative_current_hp = new_hp
                if ent:
                    ent["hp"] = new_hp

                # Send HP update to client only for real gain
                if actual_gain > 0:
                    _send_player_hp_update(session, actual_gain)
                print(f"[Loot] {char['name']} healed +{actual_gain} HP (Final: {new_hp}/{max_hp}).")
            print(
                f"[Loot] {char['name']} picked up health globe "
                f"(orb={hp_gain}, applied={actual_gain}, hp={session.authoritative_current_hp}/{max_hp})."
            )
             
        if "gear" in loot:
            gear_id = loot["gear"]
            tier = loot.get("tier", 1)
            
            # Create gear object
            new_gear = {
                "gearID": gear_id,
                "tier": tier,
                "runes": [0, 0, 0],
                "colors": [0, 0]
            }
            
            # Add to inventory
            if "inventoryGears" not in char:
                char["inventoryGears"] = []
            
            char["inventoryGears"].append(new_gear)
            
            # Trigger client notification "Received New Item"
            send_gear_reward(session, gear_id, tier=tier)
            
            save_needed = True
            print(f"[Loot] {char['name']} picked up Gear {gear_id} (Tier {tier}).")
             
        if "material" in loot:
            mat_id = loot["material"]
            
            # Add to inventory
            mats = char.setdefault("materials", [])
            found = False
            for entry in mats:
                if entry["materialID"] == mat_id:
                    entry["count"] = int(entry.get("count", 0)) + 1
                    found = True
                    break
            if not found:
                mats.append({"materialID": mat_id, "count": 1})
            
            send_material_reward(session, mat_id)
            save_needed = True
            print(f"[Loot] {char['name']} picked up Material {mat_id}.")

        if save_needed:
            active_name = char.get("name")
            if active_name:
                for c in session.char_list:
                    if c.get("name") == active_name:
                        c.update(char)
                        break
            # Keep session copy in sync for any downstream logic using current_char_dict.
            session.current_char_dict = char
            save_characters(session.user_id, session.char_list)
    else:
        # print(f"Unknown loot pick up {loot_id}")
        pass

#TODO...
def handle_queue_potion(session, data):
    br = BitReader(data[4:])
    queued_potion_id = br.read_method_20(class_3.const_69)
    #print(f"queued potion ID : {queued_potion_id}")

# Resolve badge key to mission ID
def handle_badge_request(session, data):
    br = BitReader(data[4:])
    badge_key = br.read_method_26()
    print(f"[0x8D] Badge request: {badge_key}")

    from missions import get_mission_id_by_name, get_mission_def
    mission_id = get_mission_id_by_name(badge_key)
    if mission_id is None:
        print(f"[Badge] Unknown badge key: {badge_key}")
        return

    char = session.current_char_dict
    if not char:
        return

    missions = char.setdefault("missions", {})
    mid_str = str(mission_id)
    m_data = missions.get(mid_str, {})

    # Already completed or turned in → skip
    state = m_data.get("state", 0)
    if state >= 2:
        print(f"[Badge] {badge_key} (ID {mission_id}) already completed for {char.get('name', '?')}")
        return

    # Ensure mission entry exists and mark active → completed
    m_data["state"] = 2
    m_data["progress"] = 1
    m_data["complete"] = 1
    missions[mid_str] = m_data

    # Send progress packet (0x83)
    bb_prog = BitBuffer()
    bb_prog.write_method_4(mission_id)
    bb_prog.write_method_4(1)  # progress = 1
    body_prog = bb_prog.to_bytes()
    pkt_prog = struct.pack(">HH", 0x83, len(body_prog)) + body_prog
    session.conn.sendall(pkt_prog)

    # Send completion packet (0x84)
    bb_comp = BitBuffer()
    bb_comp.write_method_4(mission_id)
    bb_comp.write_method_11(0, 1)  # IsDungeon = false
    body_comp = bb_comp.to_bytes()
    pkt_comp = struct.pack(">HH", 0x84, len(body_comp)) + body_comp
    session.conn.sendall(pkt_comp)

    save_characters(session.user_id, session.char_list)
    print(f"[Badge] {char.get('name', '?')} achieved badge: {badge_key} (Mission {mission_id}) COMPLETED!")
def handle_power_use(session, data):
    br = BitReader(data[4:])
    power = br.read_method_20(PowerType.const_423)
    #print(f"power : {power}")


#TODO...
def handle_talk_to_npc(session, data):

    br = BitReader(data[4:])
    npc_id = br.read_method_9()
    level_name = getattr(session, "current_level", None)

    npc = session.entities.get(npc_id)
    if not npc:
        # Fallback for client-spawned levels (NewbieRoad, etc.)
        # where NPCs exist in static data but not in session.entities
        npc = get_npc_props(session.current_level, npc_id)

    # Absolute lock for SwampRoadNorth Halloween ranking statues.
    locked_story_key, locked_source = _resolve_locked_story_npc_key(
        session,
        npc_id,
        level_name,
        npc=npc,
        client_ent_id=getattr(session, "clientEntID", None),
    )
    if locked_story_key:
        _send_story_npc_dialog(session, npc_id, locked_story_key, locked_source)
        return

    # Fallback for client-side static NPCs (baked into Flash SWF)
    if not npc:
        if _is_story_npc_level(level_name):
            base_idx = npc_id >> 16
            print(
                f"[{session.addr}] [PKT0x7A] STORY NPC resolve miss in {level_name}: "
                f"npc_id={npc_id}, base_idx={base_idx}, mod186={base_idx % 186}"
            )

        mapped_name, _ = _resolve_index_mapped_npc_name(
            npc_id,
            level_name,
            client_ent_id=getattr(session, "clientEntID", None),
        )
        if mapped_name:
            story_key = _canonical_story_npc_key(mapped_name)
            if story_key:
                _send_story_npc_dialog(session, npc_id, story_key, "INDEX-FALLBACK")
                return
            npc_key = _resolve_regular_npc_chat_key(mapped_name, npc_id=npc_id)
            mapped_lines = _build_npc_dialog_pool(npc_key, mapped_name)
            _send_regular_npc_dialog(
                session,
                npc_id,
                npc_key,
                mapped_lines,
                "INDEX-FALLBACK",
                raw_name=mapped_name,
            )
            return

        if _is_story_npc_level(level_name):
            # Hard guarantee: story statues in SwampRoadNorth should never fall back to generic unknown chat.
            guessed_story_key, _ = _guess_story_key_nearest(
                npc_id,
                level_name,
                baseline_player_idx=_get_cached_story_player_idx(session, level_name),
            )
            if guessed_story_key:
                _cache_story_statue_id(session, level_name, npc_id, guessed_story_key)
                _send_story_npc_dialog(session, npc_id, guessed_story_key, "LOCKED-GUESS")
            else:
                print(
                    f"[{session.addr}] [PKT0x7A] STORY NPC unresolved in {level_name}: "
                    f"npc_id={npc_id} (generic fallback blocked)"
                )
            return

        unknown_key = f"unknownnpc{npc_id}"
        unknown_lines = _build_npc_dialog_pool(unknown_key, "Wanderer")
        _send_regular_npc_dialog(
            session,
            npc_id,
            unknown_key,
            unknown_lines,
            "UNKNOWN",
            raw_name="Wanderer",
        )
        return

    # NPC internal type name:
    # This is the ONLY correct name to compare missions with.
    ent_type = (
        npc.get("character_name")
        or (npc.get("cue_data") or {}).get("character_name")
        or npc.get("entType")
        or npc.get("name")
    )

    # Normalize
    def norm(x):
        return _norm_npc_key(x)

    npc_type_norm = norm(ent_type)
    story_key = None
    for candidate in _derive_npc_lookup_keys(npc_type_norm):
        canonical = _canonical_story_npc_key(candidate)
        if canonical:
            story_key = canonical
            break

    if story_key:
        _send_story_npc_dialog(session, npc_id, story_key, "ENTITY")
        return

    # Default values
    dialogue_id = 0
    mission_id = 0

    # Highest priority state discovered so far
    # Priorities: 4 (Return Text), 3 (Active Text), 2 (Offer Text), 1 (Praise Text), 0 (None)
    highest_priority = 0
    
    char_data = session.current_char_dict or {}
    
    # We must import to get the total number of missions to evaluate
    from missions import get_total_mission_defs
    total_missions = get_total_mission_defs()

    # For mission matching, we need to handle aliases where the SWF entType 
    # doesn't match the MissionTypes.json ContactName/ReturnName.
    MISSION_NPC_ALIASES = {
        "mayorristas": "nrmayor01",
        "mayor": "nrmayor01",
        "anna": "nranna03",
        "pecky": "nrpecky",
        "captainfink": "nrcaptfink",
        "fink": "nrcaptfink",
    }
    mission_npc_norm = MISSION_NPC_ALIASES.get(npc_type_norm, npc_type_norm)

    # Pass over all missions (not just accepted ones)
    for mid in range(1, total_missions + 1):
        mextra = get_mission_extra(mid)
        if not mextra:
            continue

        # Mission-side names
        contact = norm(mextra.get("ContactName"))
        ret     = norm(mextra.get("ReturnName"))

        # Normalize them BEFORE matching (auto-map via character_name)
        if contact and contact != mission_npc_norm:
            # Allow character_name to solve mismatches
            if norm(mextra.get("ContactName")) == norm(npc.get("character_name")):
                contact = mission_npc_norm
        if ret and ret != mission_npc_norm:
            if norm(mextra.get("ReturnName")) == norm(npc.get("character_name")):
                ret = mission_npc_norm

        # Mission state (0=not accepted, 1=active, 2=completed)
        state = _get_mission_state(char_data, mid)

        # Match: Returning the mission (Highest priority: 4)
        if mission_npc_norm == ret and state == 1:
            if highest_priority < 4:
                highest_priority = 4
                dialogue_id = 4  # ReturnText
                mission_id = mid
        
        # Match: Active/In Progress (Priority: 3)
        if mission_npc_norm == contact and state == 1:
            if highest_priority < 3:
                highest_priority = 3
                dialogue_id = 3  # ActiveText
                mission_id = mid

        # Match: Offering the mission (Priority: 2)
        if mission_npc_norm == contact and state == 0:
            if highest_priority < 2:
                # IMPORTANT: We must NOT set mission_id = 0 here. 
                # We need the mission_id so the auto-accept hook below works.
                highest_priority = 2
                dialogue_id = 2  # OfferText
                mission_id = mid

        # Match: Completed/Praise (Priority: 1)
        if (mission_npc_norm == contact or mission_npc_norm == ret) and state == 2:
            if highest_priority < 1:
                highest_priority = 1
                dialogue_id = 5  # PraiseText
                mission_id = mid

    # Mission-side state updates for early Newbie Road story chain
    if dialogue_id != 0 and mission_id and mission_id in EARLY_STORY_MISSION_IDS:
        char = session.current_char_dict or {}
        current_state = _get_mission_state(char, mission_id)
        from globals import send_mission_added, send_mission_complete

        # Accept mission on first OfferText
        if dialogue_id == 2 and current_state == Mission.const_213:
            if _can_start_mission(char, mission_id):
                _set_mission_state(char, mission_id, Mission.const_58, curr_count=0)
                _persist_char_missions(session, char)
                send_mission_added(session, mission_id)

        # Turn in mission on ReturnText
        elif dialogue_id == 4 and current_state == Mission.const_58:
            _set_mission_state(char, mission_id, Mission.const_72)
            _persist_char_missions(session, char)
            send_mission_complete(session, mission_id)

    # Fallback: Bubble Chat if no mission dialogue is triggered
    if dialogue_id == 0:
        npc_key = _resolve_regular_npc_chat_key(ent_type, npc_id=npc_id)
        all_lines = _build_npc_dialog_pool(npc_key, ent_type)

        _send_regular_npc_dialog(
            session,
            npc_id,
            npc_key,
            all_lines,
            "BUBBLE",
            raw_name=ent_type,
        )
        return

    pkt = build_start_skit_packet(npc_id, dialogue_id, mission_id)
    session.conn.sendall(pkt)

    print(
        f"[{session.addr}] [PKT0x7A] TalkToNPC id={npc_id} entType={ent_type} → "
        f"dialogue_id={dialogue_id}, mission_id={mission_id}"
    )


def handle_lockbox_reward(session, data):
    _ = data[4:]
    CAT_BITS = 3
    ID_BITS = 6
    PACK_ID = 1
    TROVE_LOCKBOX_ID = 1
    
    # All legendary dyes (rarity "L") from Game.swz.txt - using DyeName format (CamelCase)
    # Client looks up dyes by DyeName, not DisplayName
    LEGENDARY_DYES = [
        "BroodMotherBlack",      # Brood Mother Black
        "ClearcastPearl",        # Clearcast Pearl
        "WizardWoolWhite",       # Wizard Wool White
        "AstralObsidian",        # Astral Obsidian
        "GleamingGold",          # Gleaming Gold
        "ShiningSilver",         # Shining Silver
        "MightyMammothIvory",    # Mighty Mammoth Ivory
        "FieryPhoenixFeather",   # Fiery Phoenix Feather
        "VelvetValkyries",       # Velvet Valkyries
        "YearOfTheMammoth",      # Year Of The Mammoth
        "CheerocracyPackPink",   # Cheerocracy Pack Pink
        "ElegantEmerald",        # Elegant Emerald
        "LeviathanLapisLazuli",  # Leviathan Lapis Lazuli
        "AlluringAmethyst",      # Alluring Amethyst
        "SparklingTourmaline",   # Sparkling Tourmaline
        "DragonCoatRed",         # Dragon Coat Red
        "IridescentOpal",        # Iridescent Opal
        "HailToTheForest",       # Hail To The Forest
        "BrokenHeartBlack",      # Broken Heart Black
        "FrostlordSatin",        # Frostlord Satin
    ]
    
    reward_map = {
        0: ("MountLockbox01L01", True, "mount"),  # Mount (Ivorstorm Guardian)
        1: ("Lockbox01L01", True, "pet"),  # Pet (Darkheart Apparition)
        2: ("GenericBrown", True, "egg"),  # Egg -> client shows "Pet (Level 10)"
        3: ("CommonBrown", True, "egg"),  # Egg
        4: ("OrdinaryBrown", True, "egg"),  # Egg
        5: ("PlainBrown", True, "egg"),  # Egg
        6: ("RarePetFood", True, "consumable"),  # Consumable
        7: ("PetFood", True, "consumable"),  # Consumable
        8: (None, True, "gear"),  # Class Gear - gear ID selected based on player class
        9: ("TripleFind", True, "charm"),  # Charm
        10: ("DoubleFind1", True, "charm"),  # Charm
        11: ("DoubleFind2", True, "charm"),  # Charm
        12: ("DoubleFind3", True, "charm"),  # Charm
        13: ("MajorLegendaryCatalyst", True, "consumable"),  # Consumable
        14: ("MajorRareCatalyst", True, "consumable"),  # Consumable
        15: ("MinorRareCatalyst", True, "consumable"),  # Consumable
        16: ("3,000,000 Gold", True, "gold", 3000000),  # Gold (3 000 000)
        17: ("1,500,000 Gold", True, "gold", 1500000),  # Gold (1 500 000)
        18: ("750,000 Gold", True, "gold", 750000),  # Gold (750 000)
        19: (None, True, "dye"),  # Legendary Dye - actual dye name selected below
    }
    
    # Class gear mapping by player class
    # Each class has 6 gear pieces: Sword, Shield, Hat, Armor, Gloves, Boots
    CLASS_GEAR_IDS = {
        "mage": [1165, 1166, 1167, 1168, 1169, 1170],
        "rogue": [1171, 1172, 1173, 1174, 1175, 1176],
        "paladin": [1177, 1178, 1179, 1180, 1181, 1182],
    }
    
    # Class gear names for client display
    CLASS_GEAR_NAMES = {
        1165: "UniqueMageLockbox01GearSword30",
        1166: "UniqueMageLockbox01GearShield30",
        1167: "UniqueMageLockbox01GearHat30",
        1168: "UniqueMageLockbox01GearArmor30",
        1169: "UniqueMageLockbox01GearGloves30",
        1170: "UniqueMageLockbox01GearBoots30",
        1171: "UniqueRogueLockbox01GearSword30",
        1172: "UniqueRogueLockbox01GearShield30",
        1173: "UniqueRogueLockbox01GearHat30",
        1174: "UniqueRogueLockbox01GearArmor30",
        1175: "UniqueRogueLockbox01GearGloves30",
        1176: "UniqueRogueLockbox01GearBoots30",
        1177: "UniquePaladinLockbox01GearSword30",
        1178: "UniquePaladinLockbox01GearShield30",
        1179: "UniquePaladinLockbox01GearHat30",
        1180: "UniquePaladinLockbox01GearArmor30",
        1181: "UniquePaladinLockbox01GearGloves30",
        1182: "UniquePaladinLockbox01GearBoots30",
    }

    # Get player class for gear selection
    char = session.current_char_dict
    if not char:
        return

    # Consume one treasure trove + one key on server side.
    # Client updates these locally too, but we must persist to disk to prevent reset on relog.
    lockboxes = char.setdefault("lockboxes", [])
    trove_entry = None
    for box in lockboxes:
        if int(box.get("lockboxID", 0)) == TROVE_LOCKBOX_ID:
            trove_entry = box
            break

    current_trove_count = int(trove_entry.get("count", 0)) if trove_entry else 0
    if current_trove_count <= 0:
        print(f"[Lockbox] {char.get('name', 'Unknown')} has no treasure troves to open")
        return

    current_keys = int(char.get("DragonKeys", 0))
    if current_keys <= 0:
        print(f"[Lockbox] {char.get('name', 'Unknown')} has no Dragon Keys to open a trove")
        return

    trove_entry["count"] = current_trove_count - 1
    if trove_entry["count"] <= 0:
        lockboxes.remove(trove_entry)

    char["DragonKeys"] = current_keys - 1
    print(
        f"[Lockbox] Consumed 1 trove + 1 key for {char.get('name', 'Unknown')} "
        f"(troves: {current_trove_count - 1}, keys: {char['DragonKeys']})"
    )
    
    player_class = char.get("class", "").lower()
    
    # ===== DUPLICATE PREVENTION FOR LEGENDARY ITEMS =====
    # Get what the player already owns
    owned_mounts = set(char.get("mounts", []))
    owned_dyes = set(char.get("OwnedDyes", []))
    owned_gear_ids = set(g.get("gearID", 0) for g in char.get("inventoryGears", []))
    owned_gear_ids.update(g.get("gearID", 0) for g in char.get("equippedGears", []))
    owned_pet_types = set(p.get("typeID", 0) for p in char.get("pets", []))
    
    # Import mount/pet/dye IDs for checking ownership
    from constants import get_mount_id, get_dye_id
    
    # Check which legendary rewards are still available
    available_rewards = {}
    
    for idx, reward_data in reward_map.items():
        reward_type = reward_data[2]
        
        if reward_type == "mount":
            mount_id = get_mount_id(reward_data[0])
            if mount_id == 0 or mount_id not in owned_mounts:
                available_rewards[idx] = reward_data
                
        elif reward_type == "pet":
            # Check if player already owns this pet type
            pet_def = next((p for p in PET_TYPES if p.get("PetName") == reward_data[0] or p.get("PetID") == reward_data[0]), None)
            if pet_def:
                pet_type_id = pet_def.get("PetID", 0)
                if pet_type_id not in owned_pet_types:
                    available_rewards[idx] = reward_data
            else:
                available_rewards[idx] = reward_data  # Unknown pet, allow it
                
        elif reward_type == "dye":
            # Dye is selected later, so we check if ANY legendary dye is available
            available_dyes = []
            for dye_name in LEGENDARY_DYES:
                dye_id = get_dye_id(dye_name)
                if dye_id == 0 or dye_id not in owned_dyes:
                    available_dyes.append(dye_name)
            if available_dyes:
                available_rewards[idx] = reward_data
                
        elif reward_type == "gear":
            # Check if any class gear is still available
            class_gears = CLASS_GEAR_IDS.get(player_class, CLASS_GEAR_IDS["paladin"])
            available_gears = [g for g in class_gears if g not in owned_gear_ids]
            if available_gears:
                available_rewards[idx] = reward_data

        elif reward_type == "egg":
            # Egg reward - adds Level 10 pet directly to inventory
            # No capacity limit for pet inventory (pets are unlimited)
            available_rewards[idx] = reward_data
                
        else:
            # Gold, consumables, charms - always available (not unique)
            available_rewards[idx] = reward_data
    
    # If no legendary rewards available, fall back to non-legendary rewards only
    if not available_rewards:
        print("[Lockbox] All legendary items owned! Falling back to non-legendary rewards.")
        available_rewards = {k: v for k, v in reward_map.items() if v[2] in ("gold", "consumable", "charm", "egg")}
    
    if not available_rewards:
        print("[Lockbox] ERROR: No rewards available at all!")
        return
    
    idx, reward_data = random.choice(list(available_rewards.items()))
    
    # For dye rewards, select a random legendary dye THE PLAYER DOESN'T OWN
    if reward_data[2] == "dye":
        available_dyes = []
        for dye_name in LEGENDARY_DYES:
            dye_id = get_dye_id(dye_name)
            if dye_id == 0 or dye_id not in owned_dyes:
                available_dyes.append(dye_name)
        if available_dyes:
            selected_dye = random.choice(available_dyes)
            reward_data = (selected_dye, True, "dye")
        else:
            # Fallback: give gold instead
            reward_data = ("750,000 Gold", True, "gold", 750000)
            idx = 18
    
    # For gear rewards, select a random class gear THE PLAYER DOESN'T OWN
    gear_id = 0
    if reward_data[2] == "gear":
        class_gears = CLASS_GEAR_IDS.get(player_class, CLASS_GEAR_IDS["paladin"])
        available_gears = [g for g in class_gears if g not in owned_gear_ids]
        if available_gears:
            gear_id = random.choice(available_gears)
            gear_name = CLASS_GEAR_NAMES.get(gear_id, f"ClassGear{gear_id}")
            reward_data = (gear_name, True, "gear", gear_id)
        else:
            # Fallback: give gold instead
            reward_data = ("750,000 Gold", True, "gold", 750000)
            idx = 18
        
    name = reward_data[0]
    needs_str = reward_data[1]
    reward_type = reward_data[2]
    gold_amount = reward_data[3] if len(reward_data) > 3 and reward_type == "gold" else 0
    reward_gear_id = reward_data[3] if len(reward_data) > 3 and reward_type == "gear" else 0
    
    # For dye rewards, do NOT convert to display name here
    # Client needs CamelCase name (e.g. "BroodMotherBlack") for icon lookup in class_18.method_996
    # Converting to "Brood Mother Black" causes Error #1009 (Null Object Reference)
    # The client handles display name conversion internally using the Dye Object
    # if reward_type == "dye":
    #    from constants import get_dye_display_name
    #    name = get_dye_display_name(name)
    
    # For egg rewards: client looks up class_14.var_233[param4] which is keyed by PetName, not EggName.
    # Sending "PlainBrown" etc. causes null lookup and Error #1009. Send the hatched pet's PetName
    # (EggID matches PetID in data) so the client can show the correct icon. Keep 'name' as egg name for grant.
    name_for_packet = name
    if reward_type == "egg":
        egg_id = get_egg_id(name)
        pet_for_display = next((p for p in PET_TYPES if p.get("PetID") == egg_id), None)
        if pet_for_display:
            name_for_packet = pet_for_display.get("PetName", name)

    # Send visual packet to client
    bb = BitBuffer()
    
    # For dye rewards, send the specific dye from the Dye Pack (Pack ID 4)
    # This allows the client to show the specific dye icon and name.
    # Lockbox legendary dye text colour: client uses Rewardpack Rarity from Game.swz.
    # DyePack01Legendary (pack 4) must have <Rarity>L</Rarity> for yellow text; see
    # extra-modules/swz-scripts/Game.swz.txt (repack into Game.swz if serving custom client).
    if reward_type == "dye":
        # Pack 4 (Dye Pack) contains a single generic dye item at index 0.
        # We must use index 0. The specific dye is determined by the name string we send.
        bb.write_method_6(4, CAT_BITS)        # Pack ID 4 = Dye Pack
        bb.write_method_6(0, ID_BITS)         # Index 0 (The only item in this pack)
    else:
        bb.write_method_6(PACK_ID, CAT_BITS)
        bb.write_method_6(idx, ID_BITS)

    
    bb.write_method_6(1 if needs_str else 0, 1)
    if needs_str:
        bb.write_method_13(name_for_packet)

    payload = bb.to_bytes()
    packet = struct.pack(">HH", 0x108, len(payload)) + payload
    session.conn.sendall(packet)

    print(f"Lockbox reward: idx={idx}, name={name}, type={reward_type}")

    
    save_needed = True
    
    
    # ALWAYS grant Royal Sigils when opening a lockbox (50-150 sigils)
    sigil_reward = random.randint(50, 150)
    current_sigils = int(char.get("SilverSigils", 0))  # Cast to int to avoid string comparison
    char["SilverSigils"] = current_sigils + sigil_reward
    
    # Send Royal Sigil reward packet (0x112)
    bb_sigil = BitBuffer()
    bb_sigil.write_method_4(sigil_reward)
    sigil_payload = bb_sigil.to_bytes()
    sigil_packet = struct.pack(">HH", 0x112, len(sigil_payload)) + sigil_payload
    session.conn.sendall(sigil_packet)
    
    save_needed = True
    print(f"[Lockbox] {char.get('name', 'Unknown')} received {sigil_reward} Royal Sigils (total: {char['SilverSigils']})")
    
    if reward_type == "gold":
        char["gold"] += gold_amount
        send_gold_reward(session, gold_amount, suppress=False)  # Show NEW notification
        save_needed = True
        print(f"[Lockbox] {char['name']} received {gold_amount} Gold")
        
    elif reward_type == "consumable":
        # Add consumable to inventory using consumableID for consistency
        from globals import send_consumable_reward
        from constants import get_consumable_id
        consumable_id = get_consumable_id(name)
        if consumable_id == 0:
            print(f"[Lockbox] Warning: Unknown consumable '{name}'")
        else:
            consumables = char.setdefault("consumables", [])
            found = False
            for entry in consumables:
                if entry.get("consumableID") == consumable_id:
                    entry["count"] = int(entry.get("count", 0)) + 1
                    found = True
                    break
            if not found:
                consumables.append({"consumableID": consumable_id, "count": 1})
            send_consumable_reward(session, name, 1)
            save_needed = True
            print(f"[Lockbox] {char['name']} received {name} (ID:{consumable_id})")
        
    elif reward_type == "charm":
        # Add charm to inventory
        from globals import send_charm_reward
        charms = char.setdefault("charms", [])
        found = False
        for entry in charms:
            if entry.get("charmName") == name:
                entry["count"] = int(entry.get("count", 0)) + 1
                found = True
                break
        if not found:
            charms.append({"charmName": name, "count": 1})
        send_charm_reward(session, name)
        save_needed = True
        print(f"[Lockbox] {char['name']} received charm {name}")
        
    elif reward_type == "mount":
        # Add mount to owned mounts
        from globals import send_mount_reward
        from constants import get_mount_id
        
        mount_id = get_mount_id(name)
        print(f"[Lockbox DEBUG] Mount lookup: name='{name}' -> mount_id={mount_id}")
        
        if mount_id != 0:
            mounts = char.setdefault("mounts", [])
            print(f"[Lockbox DEBUG] Current mounts: {mounts}")
            
            if mount_id not in mounts:
                mounts.append(mount_id)
                save_needed = True
                print(f"[Lockbox] {char['name']} received NEW mount {name} (ID: {mount_id})")
            else:
                print(f"[Lockbox] {char['name']} already owns mount {name} (ID: {mount_id})")
            
            # Always send notification for lockbox rewards (suppress=False)
            send_mount_reward(session, mount_id, suppress=False)
        else:
            print(f"[Lockbox] Warning: Unknown mount ID for {name}, skipping grant")
            
    elif reward_type == "pet":
        # Add pet to owned pets (level 1)
        pet_def = next((p for p in PET_TYPES if p.get("PetName") == name or p.get("PetID") == name), None)
        if pet_def:
            pet_type_id = pet_def["PetID"]
            starting_rank = 1
            
            pets = char.get("pets", [])
            special_id = max((p.get("special_id", 0) for p in pets), default=0) + 1
            
            new_pet = {
                "typeID": pet_type_id,
                "special_id": special_id,
                "level": starting_rank,
                "xp": 0,
            }
            
            pets.append(new_pet)
            char["pets"] = pets
            
            # Send pet notification with suppress=False to show NEW in bottom-left panel
            send_new_pet_packet(session, pet_type_id, special_id, starting_rank, suppress=False)
            save_needed = True
            print(f"[Lockbox] {char['name']} received pet {name}")
        else:
            print(f"[Lockbox] Warning: Pet definition not found for '{name}'")

    elif reward_type == "egg":
        # Egg reward - Add as Level 10 pet directly to inventory
        # (EggID matches PetID in data, so egg_id is the pet type ID)
        egg_id = get_egg_id(name)
        if egg_id and egg_id > 0:
            pet_def = next((p for p in PET_TYPES if p.get("PetID") == egg_id), None)
            if pet_def:
                pet_type_id = pet_def["PetID"]
                starting_level = 10  # Level 10 from egg reward
                
                pets = char.get("pets", [])
                special_id = max((p.get("special_id", 0) for p in pets), default=0) + 1
                
                new_pet = {
                    "typeID": pet_type_id,
                    "special_id": special_id,
                    "level": starting_level,
                    "xp": 0,
                }
                
                pets.append(new_pet)
                char["pets"] = pets
                
                # Send pet notification
                send_new_pet_packet(session, pet_type_id, special_id, starting_level, suppress=False)
                save_needed = True
                print(f"[Lockbox] {char['name']} received level {starting_level} pet {pet_def.get('DisplayName', name)}")
            else:
                print(f"[Lockbox] Warning: Pet definition not found for egg ID {egg_id}")
        else:
            print(f"[Lockbox] Warning: Unknown egg '{name}'")

    elif reward_type == "dye":
        # Add dye to OwnedDyes using integer ID (not string name)
        from globals import send_dye_reward
        from constants import get_dye_id
        
        dye_id = get_dye_id(name)
        if dye_id == 0:
            print(f"[Lockbox] Warning: Unknown dye ID for '{name}'")
        else:
            owned_dyes = char.setdefault("OwnedDyes", [])
            if dye_id not in owned_dyes:
                owned_dyes.append(dye_id)
                send_dye_reward(session, name, suppress=False)  # Show NEW notification - client uses dye's rarity
                save_needed = True
                print(f"[Lockbox] {char['name']} received dye {name} (ID: {dye_id})")
            else:
                print(f"[Lockbox] {char['name']} already owns dye {name} (ID: {dye_id})")
    
    elif reward_type == "gear":
        # Add class gear to inventory (Tier 2 = Legendary)
        if reward_gear_id > 0:
            new_gear = {
                "gearID": reward_gear_id,
                "tier": 2,  # Tier 2 = Legendary (gold/yellow notification)
                "runes": [0, 0, 0],
                "colors": [0, 0]
            }
            
            inventory = char.setdefault("inventoryGears", [])
            inventory.append(new_gear)
            
            # Send gear reward notification with tier 2 for legendary color
            send_gear_reward(session, reward_gear_id, tier=2)
            save_needed = True
            print(f"[Lockbox] {char['name']} received legendary class gear {name} (ID: {reward_gear_id}, Tier: 2)")
    
    if save_needed:
        save_characters(session.user_id, session.char_list)


def handle_buy_treasure_trove(session, data):
    """
    Handle the 0x114 packet for buying treasure troves.
    Payload contains a single byte indicating the purchase option.
    Options: x1 = 50,000 gold, x10 = 375,000 gold, x25 = 625,000 gold
    """
    raw_payload = data[4:]
    print(f"[BuyTrove DEBUG] Raw payload length: {len(raw_payload)} bytes")
    if raw_payload:
        # Print all bits for analysis
        all_bits = ''.join(format(b, '08b') for b in raw_payload)
        print(f"[BuyTrove DEBUG] Raw bits: {all_bits}")
        print(f"[BuyTrove DEBUG] Raw hex: {raw_payload.hex()}")
    
    br = BitReader(raw_payload)
    
    # Try different reading strategies to understand the packet format
    # Strategy 1: Read first 8 bits as raw value
    if len(raw_payload) >= 1:
        first_byte = raw_payload[0]
        print(f"[BuyTrove DEBUG] First byte value: {first_byte}")
    
    # Read lockbox_id (2 bits)
    lockbox_id = br.read_method_6(2)
    print(f"[BuyTrove DEBUG] lockbox_id={lockbox_id} (2 bits), remaining: {br.remaining_bits()}")
    
    # Try reading option with method_4 (variable length) instead of fixed 2 bits
    option_index = br.read_method_4()
    print(f"[BuyTrove DEBUG] option_index={option_index} (method_4)")
    
    print(f"[BuyTrove] Received: lockbox_id={lockbox_id}, option_index={option_index}")
    
    # Define costs and quantities
    TROVE_OPTIONS = {
        0: {"quantity": 1, "cost": 50000},
        1: {"quantity": 10, "cost": 375000},
        2: {"quantity": 25, "cost": 625000},
    }
    
    if option_index not in TROVE_OPTIONS:
        print(f"[BuyTrove] Invalid option index: {option_index}")
        return
    
    option = TROVE_OPTIONS[option_index]
    quantity = option["quantity"]
    cost = option["cost"]
    
    char = session.current_char_dict
    if not char:
        print("[BuyTrove] No character data found")
        return
    
    current_gold = int(char.get("gold", 0))
    
    if current_gold < cost:
        print(f"[BuyTrove] Not enough gold: {current_gold} < {cost}")
        return
    
    # Deduct gold
    char["gold"] = current_gold - cost
    
    # Add treasure troves (lockboxID = 1 for standard treasure trove)
    TROVE_LOCKBOX_ID = 1
    lockboxes = char.setdefault("lockboxes", [])
    
    # Find existing lockbox entry or create new one
    found = False
    for box in lockboxes:
        if box.get("lockboxID") == TROVE_LOCKBOX_ID:
            box["count"] = int(box.get("count", 0)) + quantity
            found = True
            break
    
    if not found:
        lockboxes.append({"lockboxID": TROVE_LOCKBOX_ID, "count": quantity})
    
    # Save character data
    save_characters(session.user_id, session.char_list)
    
    # Send gold loss notification to client (packet 0xB4)
    bb = BitBuffer()
    bb.write_method_4(cost)
    payload = bb.to_bytes()
    packet = struct.pack(">HH", 0xB4, len(payload)) + payload
    session.conn.sendall(packet)
    
    # Send lockbox inventory update to client (packet 0x104)
    # Client reads: method_6(class_15.const_300) = 2 bits for lockbox ID
    #              method_4() for count (this is the DELTA to add, not total!)
    #              method_11() for boolean flag (show notification)
    bb_lockbox = BitBuffer()
    bb_lockbox.write_method_6(TROVE_LOCKBOX_ID, 2)  # 2 bits for lockbox ID
    # Send the quantity purchased (delta), NOT the total count
    # Client adds this value to its local count
    bb_lockbox.write_method_4(quantity)
    bb_lockbox.write_method_11(1, 1)  # Show notification = true
    lockbox_payload = bb_lockbox.to_bytes()
    lockbox_packet = struct.pack(">HH", 0x104, len(lockbox_payload)) + lockbox_payload
    session.conn.sendall(lockbox_packet)
    
    # Calculate new total for logging
    new_count = 0
    for box in lockboxes:
        if box.get("lockboxID") == TROVE_LOCKBOX_ID:
            new_count = int(box.get("count", 0))
            break
    
    print(f"[BuyTrove] {char.get('name', 'Unknown')} purchased {quantity} treasure trove(s) for {cost} gold (new total: {new_count})")


def handle_buy_lockbox_keys(session, data):
    """
    Handle the 0x105 packet for buying lockbox keys with Mammoth Idols.
    Client sends: method_9(option_index) ONLY - no lockbox_id!
    Client adds keys locally and expects NO response packet.
    Options from const_356 = [1, 10, 25], costs from const_1059 = [22, 210, 470]
    """
    raw_payload = data[4:]
    print(f"[BuyKeys DEBUG] Raw payload length: {len(raw_payload)} bytes")
    if raw_payload:
        all_bits = ''.join(format(b, '08b') for b in raw_payload)
        print(f"[BuyKeys DEBUG] Raw bits: {all_bits}")
    
    br = BitReader(raw_payload)
    
    # Client sends ONLY option_index via method_9 (4-bit prefix + variable value)
    # NOT lockbox_id + option_index as previously assumed
    option_index = br.read_method_9()
    print(f"[BuyKeys DEBUG] option_index={option_index}")
    
    # Define costs and quantities for keys
    # From class_131.txt: const_356 = [1, 10, 25], const_1059 = [22, 210, 470]
    KEY_OPTIONS = {
        0: {"quantity": 1, "cost": 22},
        1: {"quantity": 10, "cost": 210},
        2: {"quantity": 25, "cost": 470},
    }
    
    if option_index not in KEY_OPTIONS:
        print(f"[BuyKeys] Invalid option index: {option_index}")
        return
    
    option = KEY_OPTIONS[option_index]
    quantity = option["quantity"]
    cost = option["cost"]
    
    char = session.current_char_dict
    if not char:
        print("[BuyKeys] No character data found")
        return
    
    current_idols = int(char.get("mammothIdols", 0))
    
    if current_idols < cost:
        print(f"[BuyKeys] Not enough Mammoth Idols: {current_idols} < {cost}")
        return
    
    # Deduct Mammoth Idols
    char["mammothIdols"] = current_idols - cost
    
    # Add Dragon Keys
    current_keys = int(char.get("DragonKeys", 0))
    char["DragonKeys"] = current_keys + quantity
    
    # Save character data
    save_characters(session.user_id, session.char_list)
    
    # Send Mammoth Idols deduction to client (packet 0xB5)
    # Client's method_1000 reads:
    #   1. method_13() - purchase name string
    #   2. method_4() - cost to deduct
    # Then: this.var_1.mMammothIdols -= cost
    bb_idols = BitBuffer()
    bb_idols.write_method_13(f"DragonKeys_x{quantity}")  # Purchase name string
    bb_idols.write_method_4(cost)  # Cost to deduct from idols
    idols_payload = bb_idols.to_bytes()
    idols_packet = struct.pack(">HH", 0xB5, len(idols_payload)) + idols_payload
    session.conn.sendall(idols_packet)
    
    print(f"[BuyKeys] {char.get('name', 'Unknown')} purchased {quantity} key(s) for {cost} Mammoth Idols")
    print(f"[BuyKeys] New totals - Keys: {char['DragonKeys']}, Idols: {char['mammothIdols']}")


def handle_hp_increase_notice(session, data):
    br = BitReader(data[4:])
    max_hp_delta = int(br.read_method_24())

    level = int((session.current_char_dict or {}).get("level", 1) or 1)
    level = max(1, min(level, len(Entity.PLAYER_HITPOINTS) - 1))
    fallback_max = int(Entity.PLAYER_HITPOINTS[level])

    current_max = int(getattr(session, "authoritative_max_hp", fallback_max) or fallback_max)
    new_max = max(1, current_max + max_hp_delta)
    session.authoritative_max_hp = new_max
    _mark_max_hp_sync(session)

    ent = session.entities.get(session.clientEntID) if session.clientEntID is not None else None
    if ent is not None:
        ent["max_hp"] = new_max
        ent_current = int(ent.get("hp", new_max) or new_max)
        ent["hp"] = min(max(0, ent_current), new_max)

    current_hp = int(getattr(session, "authoritative_current_hp", new_max) or new_max)
    session.authoritative_current_hp = min(max(0, current_hp), new_max)

    pending_orb_heal = getattr(session, "pending_orb_heal", None)
    if pending_orb_heal and pending_orb_heal.get("wait_for_max_sync"):
        _request_client_hp_report(session)


def handle_client_hp_report(session, data):
    br = BitReader(data[4:])
    client_curr_hp = int(br.read_method_24())

    # Client also sends a small reason/source field + a bool flag; consume to keep parser aligned.
    _ = br.read_method_20(Game.const_390)
    _ = br.read_method_15()

    level = int((session.current_char_dict or {}).get("level", 1) or 1)
    level = max(1, min(level, len(Entity.PLAYER_HITPOINTS) - 1))
    fallback_max = int(Entity.PLAYER_HITPOINTS[level])
    max_hp = int(getattr(session, "authoritative_max_hp", fallback_max) or fallback_max)
    if max_hp <= 0:
        max_hp = fallback_max
        session.authoritative_max_hp = max_hp

    synced_hp = min(max(0, client_curr_hp), max_hp)
    session.authoritative_current_hp = synced_hp
    session.last_client_hp_report_ts = time.time()
    session.last_client_hp_report_value = synced_hp

    active_ent_id = _resolve_active_player_entity_id(session)
    ent = session.entities.get(active_ent_id) if active_ent_id is not None else None
    if ent is not None:
        ent["max_hp"] = max_hp
        ent["hp"] = synced_hp

    pending_orb_heal = getattr(session, "pending_orb_heal", None)
    if pending_orb_heal:
        now = time.time()
        expires_at = float(pending_orb_heal.get("expires_at", 0.0) or 0.0)
        wait_for_max_sync = bool(pending_orb_heal.get("wait_for_max_sync", False))
        pending_level = pending_orb_heal.get("level")
        entries = []
        raw_entries = pending_orb_heal.get("entries")
        if isinstance(raw_entries, list):
            for entry in raw_entries:
                if not isinstance(entry, dict):
                    continue
                amount = int(entry.get("amount", 0) or 0)
                if amount <= 0:
                    continue
                queued_at = float(entry.get("queued_at", now) or now)
                picked_at_full = bool(entry.get("picked_at_full", False))
                entries.append({
                    "amount": amount,
                    "queued_at": queued_at,
                    "picked_at_full": picked_at_full,
                })
        if not entries:
            amount = int(pending_orb_heal.get("amount", 0) or 0)
            if amount > 0:
                entries = [{
                    "amount": amount,
                    "queued_at": float(pending_orb_heal.get("queued_at", now) or now),
                    "picked_at_full": bool(pending_orb_heal.get("picked_at_full", False)),
                }]

        if pending_level and pending_level != getattr(session, "current_level", None):
            session.pending_orb_heal = None
            return

        if now > expires_at:
            session.pending_orb_heal = None
            return

        if wait_for_max_sync and not _has_max_hp_sync_for_current_level(session):
            _request_client_combat_stats_sync(session)
            return

        session.pending_orb_heal = None

        any_full_pick = any(bool(e.get("picked_at_full")) for e in entries)
        current_hp = int(synced_hp)
        applied_total = 0
        applied_count = 0
        if entries and current_hp < max_hp:
            for entry in entries:
                if current_hp >= max_hp:
                    break
                amount = int(entry.get("amount", 0) or 0)
                if amount <= 0:
                    continue
                if entry.get("picked_at_full"):
                    report_delay = max(0.0, now - float(entry.get("queued_at", now) or now))
                    print(
                        f"[HP DriftFix] Reconcile full-pick orb: "
                        f"client report below max after {report_delay:.3f}s "
                        f"({current_hp}/{max_hp})."
                    )
                apply_gain = min(max_hp - current_hp, amount)
                if apply_gain <= 0:
                    continue
                current_hp += apply_gain
                applied_total += apply_gain
                applied_count += 1
                _send_player_hp_update(session, apply_gain)

            if applied_total > 0:
                session.authoritative_current_hp = current_hp
                if ent is not None:
                    ent["hp"] = current_hp
                print(
                    f"[HP DriftFix] Applied delayed orb heal +{applied_total} "
                    f"after client HP report ({current_hp}/{max_hp}, orbs={applied_count})."
                )
        elif any_full_pick:
            print(
                f"[HP DriftFix] Skipped delayed orb heal: picked at full HP "
                f"(report={synced_hp}/{max_hp})."
            )


#TODO...
def handle_linkupdater(session, data):
    return  # return here no point doing anything here for now at least

    br = BitReader(data[4:])

    client_elapsed = br.read_method_24()
    client_desync  = br.read_method_15()
    server_echo    = br.read_method_24()

    now_ms = int(time.time() * 1000)

    # First update → establish baseline
    if not hasattr(session, "clock_base"):
        session.clock_base = now_ms
        session.clock_offset_ms = 0
        session.last_desync_time = None

    session.client_elapsed = client_elapsed
    session.server_elapsed = server_echo

    # Compute offset (server_time - expected_client_time)
    session.clock_offset_ms = now_ms - (session.clock_base + client_elapsed)
    offset = abs(session.clock_offset_ms)

    DESYNC_THRESHOLD = 2500     # ms allowed before warning
    DESYNC_KICK_TIME = 2.0      # seconds of continuous desync before kick

    if offset > DESYNC_THRESHOLD or client_desync:
        # First time detecting desync
        if session.last_desync_time is None:
            session.last_desync_time = time.time()
            print(f"[{session.addr}] Desync detected offset={offset}ms (timer started)")
        else:
            elapsed = time.time() - session.last_desync_time
            if elapsed >= DESYNC_KICK_TIME:
                print(f"[{session.addr}] Kicking player for severe desync (offset={offset}ms)")
                session.conn.close()
                session.stop()
                return

    props = {
        "client_elapsed": client_elapsed,
        "client_desync": client_desync,
        "server_echo": server_echo,
        "clock_base": getattr(session, "clock_base", None),
        "server_now_ms": now_ms,
        "client_offset_ms": session.clock_offset_ms,
    }

    #print(f"Player [{get_active_character_name(session)}]")
    #pprint.pprint(props, indent=4)

#TODO... this is just for testing
_last_loot_id = 900000
def generate_loot_id():
    global _last_loot_id
    _last_loot_id += 1
    return _last_loot_id

def handle_grant_reward(session, data):
    br = BitReader(data[4:])

    receiver_id = br.read_method_9()
    source_id   = br.read_method_9()

    drop_item   = br.read_method_15()
    item_mult   = br.read_method_309()

    drop_gear   = br.read_method_15()
    gear_mult   = br.read_method_309()

    drop_material = br.read_method_15()
    drop_trove    = br.read_method_15()

    exp     = br.read_method_9()
    pet_exp = br.read_method_9()
    hp_gain = br.read_method_9()
    gold    = br.read_method_9()

    world_x = br.read_method_24()
    world_y = br.read_method_24()

    killing_blow = br.read_method_15()
    combo = br.read_method_9() if killing_blow else 0

    # Deduplication: Check if this source has already been processed in this level
    if not hasattr(session, "processed_reward_sources"):
        session.processed_reward_sources = set()
    
    # Check if the NPC exists and has already granted rewards (Authoritative Check)
    npc = get_npc_props(session.current_level, source_id)
    if npc:
        # Only allow reward if server marked the kill
        if not npc.get("rewards_granted", False):
            hp_val = npc.get("hp")
            if hp_val is None or hp_val > 0:
                print(f"[EXPLOIT PREVENTED] {session.addr} attempted GRANT_REWARD for alive NPC {source_id}.")
                return
            # Mark now to allow a single grant if hp <= 0
            npc["rewards_granted"] = True
        else:
            print(f"[EXPLOIT PREVENTED] {session.addr} tried to claim rewards from {source_id} again.")
            return

    reward_key = (session.current_level, source_id)
    if reward_key in session.processed_reward_sources:
        return
    session.processed_reward_sources.add(reward_key)

    # Physical Drops Only: We no longer add gold/xp directly to the character here.
    # Everything must be collected via physical loot drops (globes/gold piles).

    # --- Hybrid Loot Drop Logic ---
    # 1. Look up the source entity (Mob) to check if it's Flying.
    # 2. Flying Mobs: Spawn at Player Y (Ground) with offset.
    # 3. Ground Mobs: Spawn at Mob X/Y (Preserve Ramp Height) from packet.
    
    from game_data import get_ent_type # ensure import available if not top-level
    
    is_flying = False
    source_ent = None
    ent_name = None
    
    # Try to find source entity
    # Check session entities first
    if source_id in session.entities:
        source_ent = session.entities[source_id]
    # Check global level NPCs
    elif session.current_level in GS.level_npcs and source_id in GS.level_npcs[session.current_level]:
        source_ent = GS.level_npcs[session.current_level][source_id]
        
    ent_name = None
    if source_ent:
        ent_name = source_ent.get("name")
        ent_type_data = get_ent_type(ent_name) or {}
        if ent_type_data.get("Flying") == "True":
            is_flying = True
    else:
        ent_type_data = {}

    # Track calculated material/gear for drops
    material_id = 0
    specific_gear_id = None
    gear_tier = 0

    # OVERRIDE: If client reports zero gold, calculate proper rewards server-side.
    # The client often sends real XP but Gold=0 and Item=False for dungeon enemies.
    if gold == 0:
        char = session.current_char_dict
        p_level = char.get("level", 1) if char else 1
        
        from game_data import calculate_npc_gold, calculate_npc_exp, calculate_drop_data, get_ent_type
        from game_data import get_random_material_for_realm, get_gear_id_for_entity
        import random
        
        # Determine dungeon level from LEVEL_CONFIG for gold scaling
        from level_config import LEVEL_CONFIG
        dungeon_cfg = LEVEL_CONFIG.get(session.current_level)
        dungeon_level = dungeon_cfg[1] if dungeon_cfg else p_level  # [1] = map_id = enemy level
        
        # Dungeon-to-Realm mapping for material drops when entity name is unknown
        DUNGEON_REALM_MAP = {
            "GoblinRiverDungeon": "Goblin", "GoblinRiverDungeonHard": "Goblin",
            "DreamDragonDungeon": "Ghost", "DreamDragonDungeonHard": "Ghost",
            "GoblinMineDungeon": "Goblin", "GoblinMineDungeonHard": "Goblin",
            "SwampCaveDungeon": "Devourer", "SwampCaveDungeonHard": "Devourer",
            "SpiderNestDungeon": "Spider", "SpiderNestDungeonHard": "Spider",
            "WyrmCaveDungeon": "Wyrm", "WyrmCaveDungeonHard": "Wyrm",
            "WolfDenDungeon": "Wolf", "WolfDenDungeonHard": "Wolf",
            "SkeletonCryptDungeon": "Skeleton", "SkeletonCryptDungeonHard": "Skeleton",
            "LizardTempleDungeon": "Lizard", "LizardTempleDungeonHard": "Lizard",
            "MummyTombDungeon": "Mummy", "MummyTombDungeonHard": "Mummy",
        }
        
        # 1. Attempt Precise Calculation using entity data
        precise_gold = 0
        precise_xp = 0
        ent_data_found = False
        
        ent_name_lookup = ent_name # from earlier scope
        if not ent_name_lookup and source_id in session.entities:
             ent_name_lookup = session.entities[source_id].get("name")
             
        if ent_name_lookup:
             # Use entity's own level from EntType if available, otherwise dungeon level
             ety = get_ent_type(ent_name_lookup) or {}
             ent_level = int(ety.get("Level", dungeon_level))
             
             precise_gold = calculate_npc_gold(ent_name_lookup, ent_level)
             precise_xp = calculate_npc_exp(ent_name_lookup, ent_level)
             if precise_gold > 0 or precise_xp > 0:
                 ent_data_found = True
                 if exp <= 1:
                     exp = precise_xp
                 gold = precise_gold
                 
                 # Recalculate Item Drops based on real data
                 drop_gear, gear_tier_val = calculate_drop_data(ent_name_lookup, ent_level)
                 if drop_gear:
                     drop_gear = True
                     gear_tier = gear_tier_val
                     specific_gear_id = get_gear_id_for_entity(ent_name_lookup)
                 
                 # Material drop (30% chance, based on entity Realm)
                 realm = ety.get("Realm")
                 if realm and realm != "PlayerPet" and random.random() < 0.30:
                     mat = get_random_material_for_realm(realm)
                     if mat:
                         material_id = mat
        
        # 2. Fallback if no entity data found (most dungeon kills)
        if not ent_data_found:
            # Use dungeon_level for gold table lookup, NOT player level
            from game_data import MONSTER_GOLD_TABLE
            idx = max(0, min(dungeon_level, len(MONSTER_GOLD_TABLE) - 1))
            base_gold = MONSTER_GOLD_TABLE[idx]
            
            # Gold: base_gold * 0.4 (minion scalar) * 0.5 + randomization
            loc10 = 0.4 * base_gold * 0.5
            calc_gold = int(loc10 + (loc10 * 2 + 1) * random.random())
            gold = max(1, calc_gold)
            
            # XP: keep client XP if it's reasonable, otherwise scale from dungeon level
            if exp <= 1:
                calc_xp = 50 + (dungeon_level * 15)
                exp = int(calc_xp * random.uniform(0.8, 1.2))
            
            # 10% chance for gear
            if random.random() < 0.10:
                 drop_gear = True
                 gear_tier = 1
            
            # 30% chance for materials based on dungeon realm
            dungeon_realm = DUNGEON_REALM_MAP.get(session.current_level)
            if dungeon_realm and random.random() < 0.30:
                mat = get_random_material_for_realm(dungeon_realm)
                if mat:
                    material_id = mat
        
        # Logic for HP orb (20% chance)
        if random.random() < 0.20:
             hp_base, current_hp_base, _ = _resolve_authoritative_hp_state(session)
             if not _has_max_hp_sync_for_current_level(session):
                 hp_base = max(100, min(hp_base, current_hp_base))
             hp_gain = int(hp_base * 0.15)
             
        print(f"[Loot Override] {receiver_id} killed {ent_name_lookup or 'Unknown'} (dungeon_lvl={dungeon_level}). Loot: XP={exp}, Gold={gold}, Item={drop_gear}, Material={material_id}")
        
    
    if is_flying:
        # Use player's X and Y coordinate (Gravity Fallback)
        player_ent = session.entities.get(session.clientEntID)
        if player_ent:
            if "pos_y" in player_ent:
                world_y = int(player_ent["pos_y"])
            if "pos_x" in player_ent:
                # Add a small random offset (30-60 pixels) so loot doesn't spawn *inside* the player
                offset = random.choice([-1, 1]) * random.randint(30, 60)
                world_x = int(player_ent["pos_x"]) + offset
    else:
        # Ground Mob: Trust the coordinates reported by client (matched to mob death)
        if source_ent and "x" in source_ent and "y" in source_ent:
             world_x = int(source_ent.get("pos_x", source_ent["x"]))
             world_y = int(source_ent.get("pos_y", source_ent["y"]))

    # ---------------------------------------------------------
    # APPLY XP REWARD (Critical for client-side mobs)
    # ---------------------------------------------------------
    if exp > 0:
        # 1. Send XP Packet to Client
        from globals import send_xp_reward
        send_xp_reward(session, exp)
        
        # 2. Update Character Data
        if session.current_char_dict:
             char = session.current_char_dict
             current_keys = char.get("xp", 0) + exp
             char["xp"] = current_keys
             
             # Check Level Up
             from game_data import get_player_level_from_xp
             old_level = char.get("level", 1)
             new_level = get_player_level_from_xp(current_keys)
             if new_level > old_level:
                 char["level"] = new_level
                 print(f"[LevelUp] {char.get('name')} {old_level}->{new_level}")

             # 3. Apply same XP to active pet (matches mob XP granted to player)
             from globals import send_pet_xp_update

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
                     pet_xp_gain = int(exp)
                     pet_xp_total = int(target_pet.get("xp", 0) or 0) + pet_xp_gain
                     target_pet["xp"] = pet_xp_total
                     current_pet_level = int(target_pet.get("level", 1) or 1)
                     active_pet_info["xp"] = pet_xp_total
                     active_pet_info["level"] = current_pet_level

                     send_pet_xp_update(
                         session,
                         pet_type_id,
                         pet_special_id,
                         pet_xp_gain,
                         current_pet_level,
                         False,
                     )
             
             save_characters(session.user_id, session.char_list)

    # NOTE: Do NOT pass target_id here. handle_grant_reward already added source_id
    # to processed_reward_sources (line ~1133). If we pass target_id, process_drop_reward
    # will find the same key in the set and return without spawning any loot.
    process_drop_reward(session, world_x, world_y, gold, hp_gain, drop_gear, material_id=material_id, gear_tier=gear_tier, specific_gear_id=specific_gear_id)
    
    print(f"Granted Reward Request for {source_id}: XP={exp}, Gold={gold}, Item={drop_gear}")

def process_drop_reward(
    session,
    x,
    y,
    gold=0,
    hp_gain=0,
    drop_gear=False,
    material_id=0,
    target_id=0,
    gear_tier=0,
    specific_gear_id=None,
    reward_nonce=None,
):
    # Normalize coordinates to ints for BitBuffer writers
    x = int(round(x))
    y = int(round(y))
    # Initialize session tracking if needed
    if not hasattr(session, "pending_loot"):
        session.pending_loot = {}
    if not hasattr(session, "processed_reward_sources"):
        session.processed_reward_sources = set()

    # Deduplication check
    if target_id != 0:
        if reward_nonce is None:
            reward_key = (session.current_level, target_id)
        else:
            reward_key = (session.current_level, target_id, int(reward_nonce))
        if reward_key in session.processed_reward_sources:
            return
        session.processed_reward_sources.add(reward_key)

    # Drop Gold
    if gold > 0:
        lid = generate_loot_id()
        # Store for pickup verification
        session.pending_loot[lid] = {"gold": gold}
        
        pkt = build_lootdrop(
            loot_id=lid,
            x=x,
            y=y,
            gold=gold
        )
        session.conn.sendall(pkt)

    # Drop Health
    if hp_gain > 0:
        lid = generate_loot_id()
        session.pending_loot[lid] = {"health": hp_gain}
        
        pkt = build_lootdrop(
            loot_id=lid,
            x=x + random.randint(-15, 15),
            y=y + random.randint(-15, 15),
            health=hp_gain
        )
        session.conn.sendall(pkt)

    # Drop Gear
    if drop_gear:
        # Only drop gear if we have a valid specific_gear_id
        # The fallback get_random_gear_id() can return IDs without valid client graphics
        if specific_gear_id and specific_gear_id > 0:
            lid = generate_loot_id()
            gear_id = specific_gear_id
            session.pending_loot[lid] = {"gear": gear_id, "tier": gear_tier}
            
            pkt = build_lootdrop(
                loot_id=lid,
                x=x + random.randint(-20, 20),
                y=y + random.randint(-10, 10),
                gear_id=gear_id, 
                gear_tier=gear_tier
            )
            session.conn.sendall(pkt)

    # Drop Material
    if material_id and material_id > 0:
        lid = generate_loot_id()
        session.pending_loot[lid] = {"material": material_id}
        
        pkt = build_lootdrop(
            loot_id=lid,
            x=x + random.randint(-20, 20),
            y=y + random.randint(-10, 10),
            material_id=material_id
        )
        session.conn.sendall(pkt)

def build_lootdrop(
        loot_id: int,
        x: int,
        y: int,
        gear_id: int = 0,
        gear_tier: int = 0,
        material_id: int = 0,
        gold: int = 0,
        health: int = 0,
        trove: int = 0,
        dye_id: int = 0
):
    bb = BitBuffer()

    bb.write_method_4(loot_id)
    bb.write_method_45(x)
    bb.write_method_45(y)

    # Gear branch
    if gear_id > 0:
        bb.write_method_15(True)
        bb.write_method_6(gear_id, GearType.GEARTYPE_BITSTOSEND)
        bb.write_method_6(gear_tier, GearType.const_176)
        body = bb.to_bytes()
        return struct.pack(">HH", 0x32, len(body)) + body
    else:
        bb.write_method_15(False)

    # Material Branch
    if material_id > 0:
        bb.write_method_15(True)
        bb.write_method_4(material_id)
        body = bb.to_bytes()
        return struct.pack(">HH", 0x32, len(body)) + body
    else:
        bb.write_method_15(False)

    # Gold Branch
    if gold > 0:
        bb.write_method_15(True)
        bb.write_method_4(gold)
        body = bb.to_bytes()
        return struct.pack(">HH", 0x32, len(body)) + body
    else:
        bb.write_method_15(False)

    # Health Branch
    if health > 0:
        bb.write_method_15(True)
        bb.write_method_4(health)
        body = bb.to_bytes()
        return struct.pack(">HH", 0x32, len(body)) + body
    else:
        bb.write_method_15(False)

    # Chest Trove Branch
    if trove > 0:
        bb.write_method_15(True)
        bb.write_method_4(trove)
        body = bb.to_bytes()
        return struct.pack(">HH", 0x32, len(body)) + body
    else:
        bb.write_method_15(False)

    # Fallback branch: dye ID
    val = dye_id if dye_id > 0 else 1
    bb.write_method_4(val)

    body = bb.to_bytes()
    return struct.pack(">HH", 0x32, len(body)) + body
