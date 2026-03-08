from __future__ import annotations

from constants import Mission
from missions import get_mission_extra


def ensure_char_missions(char: dict) -> dict:
    missions = char.get("missions")
    if not isinstance(missions, dict):
        missions = {}
        char["missions"] = missions
    return missions


def mission_requires_turn_in(mission_id: int) -> bool:
    extra = get_mission_extra(mission_id) or {}
    return bool(str(extra.get("ReturnName") or "").strip())


def normalize_mission_entry(mission_id: int, entry: dict | None) -> dict:
    normalized = dict(entry) if isinstance(entry, dict) else {}
    try:
        state = int(normalized.get("state", Mission.const_213))
    except Exception:
        state = Mission.const_213

    if state <= Mission.const_213:
        normalized["state"] = Mission.const_213
        return normalized

    if state == Mission.const_58:
        normalized["state"] = Mission.const_58
        normalized.pop("claimed", None)
        normalized.pop("complete", None)
        return normalized

    if state == Mission.const_72:
        legacy_claimed = bool(normalized.get("claimed")) or bool(normalized.get("complete"))
        if legacy_claimed or not mission_requires_turn_in(mission_id):
            normalized["state"] = Mission.CLAIMED
            normalized["claimed"] = 1
            normalized["complete"] = 1
        else:
            normalized["state"] = Mission.const_72
            normalized.pop("claimed", None)
            normalized.pop("complete", None)
        return normalized

    normalized["state"] = Mission.CLAIMED
    normalized["claimed"] = 1
    normalized["complete"] = 1
    return normalized


def normalize_char_missions(char: dict) -> dict:
    missions = ensure_char_missions(char)
    for mid_str in list(missions.keys()):
        entry = missions.get(mid_str)
        try:
            mission_id = int(mid_str)
        except Exception:
            continue

        normalized = normalize_mission_entry(mission_id, entry)
        if normalized.get("state", Mission.const_213) <= Mission.const_213:
            missions.pop(mid_str, None)
            continue
        missions[mid_str] = normalized
    return missions


def get_mission_entry(char: dict, mission_id: int) -> dict:
    missions = normalize_char_missions(char)
    entry = missions.get(str(mission_id))
    return entry if isinstance(entry, dict) else {}


def get_mission_state(char: dict, mission_id: int) -> int:
    entry = get_mission_entry(char, mission_id)
    try:
        return int(entry.get("state", Mission.const_213))
    except Exception:
        return Mission.const_213


def set_mission_state(
    char: dict,
    mission_id: int,
    state: int,
    curr_count: int | None = None,
    tier: int | None = None,
    highscore: int | None = None,
    time_value: int | None = None,
) -> None:
    missions = ensure_char_missions(char)
    entry = normalize_mission_entry(mission_id, missions.get(str(mission_id)))
    entry["state"] = int(state)

    if curr_count is not None:
        entry["currCount"] = int(curr_count)
    if tier is not None:
        entry["Tier"] = int(tier)
    if highscore is not None:
        entry["highscore"] = int(highscore)
    if time_value is not None:
        entry["Time"] = int(time_value)

    if int(state) >= Mission.CLAIMED:
        entry["claimed"] = 1
        entry["complete"] = 1
    else:
        entry.pop("claimed", None)
        entry.pop("complete", None)

    missions[str(mission_id)] = entry
    normalize_char_missions(char)


def mission_has_started(char: dict, mission_id: int) -> bool:
    return get_mission_state(char, mission_id) != Mission.const_213


def mission_is_ready_to_turn_in(char: dict, mission_id: int) -> bool:
    return get_mission_state(char, mission_id) == Mission.const_72


def mission_is_completed(char: dict, mission_id: int) -> bool:
    return get_mission_state(char, mission_id) >= Mission.CLAIMED


def completion_state_for_objective(mission_id: int) -> int:
    if mission_requires_turn_in(mission_id):
        return Mission.const_72
    return Mission.CLAIMED
