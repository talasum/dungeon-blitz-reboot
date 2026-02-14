import os
import json
import struct
import tempfile

from threading import Lock
from BitBuffer import BitBuffer

SAVE_PATH_TEMPLATE = "saves/{user_id}.json"
CHAR_SAVE_DIR = "saves"
_ACCOUNTS_PATH = "Accounts.json"
_lock          = Lock()

def _write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", suffix=".json", dir=os.path.dirname(path) or ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def _load_json_resilient(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read().lstrip("\ufeff \t\r\n")
            decoder = json.JSONDecoder()
            parsed, _ = decoder.raw_decode(raw)
            backup = f"{path}.corrupt"
            try:
                os.replace(path, backup)
            except OSError:
                pass
            _write_json(path, parsed)
            return parsed
        except Exception:
            return default


def load_accounts() -> dict[str, int]:
    if not os.path.exists(_ACCOUNTS_PATH):
        
        with open(_ACCOUNTS_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)

    with _lock:
        entries = _load_json_resilient(_ACCOUNTS_PATH, [])

    return {e["email"]: int(e["user_id"]) for e in entries}


def save_accounts_index(index: dict[str, int]) -> None:
    entries = [
        {"email": email, "user_id": uid}
        for email, uid in index.items()
    ]
    with _lock:
        _write_json(_ACCOUNTS_PATH, entries)

def get_or_create_user_id(email: str) -> int:
    email = email.strip().lower()
    accounts = load_accounts()

    if email in accounts:
        return accounts[email]

    user_id = max(accounts.values(), default=0) + 1

    accounts[email] = user_id
    save_accounts_index(accounts)

    os.makedirs(CHAR_SAVE_DIR, exist_ok=True)
    save_path = os.path.join(CHAR_SAVE_DIR, f"{user_id}.json")
    _write_json(save_path, {"user_id": user_id, "characters": []})
    return user_id

def is_character_name_taken(name: str) -> bool:
    """
    Check if a character name exists in any user's save file.
    """
    name = name.strip().lower()
    accounts = load_accounts()
    for user_id in accounts.values():
        save_path = os.path.join(CHAR_SAVE_DIR, f"{user_id}.json")
        try:
            with open(save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                characters = data.get("characters", [])
                for char in characters:
                    if char.get("name", "").strip().lower() == name:
                        return True
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return False

def build_popup_packet(message: str, disconnect: bool = False) -> bytes:
    buf = BitBuffer(debug=True)
    buf.write_method_13(message)
    buf.write_method_6(1 if disconnect else 0, 1)
    payload = buf.to_bytes()
    return struct.pack(">HH", 0x1B, len(payload)) + payload


def load_characters(user_id: int) -> list[dict]:
    path = os.path.join(CHAR_SAVE_DIR, f"{user_id}.json")
    if not os.path.exists(path):
        return []
    with _lock:
        data = _load_json_resilient(path, {"user_id": user_id, "characters": []})
    return data.get("characters", [])


def save_characters(user_id: int, char_list: list[dict]):
    os.makedirs(CHAR_SAVE_DIR, exist_ok=True)
    path = os.path.join(CHAR_SAVE_DIR, f"{user_id}.json")

    data = {
        "user_id": user_id,
        "characters": char_list
    }

    with _lock:
        _write_json(path, data)


def find_user_by_character_name(name: str):
    """
    Finds a user and their character list by character name.
    Returns (user_id, char_list, specific_char) or (None, None, None).
    """
    name = name.strip().lower()
    accounts = load_accounts()
    for user_id in accounts.values():
        save_path = os.path.join(CHAR_SAVE_DIR, f"{user_id}.json")
        if not os.path.exists(save_path):
            continue
            
        try:
            with open(save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            characters = data.get("characters", [])
            for char in characters:
                if char.get("name", "").strip().lower() == name:
                    return user_id, characters, char
        except (FileNotFoundError, json.JSONDecodeError):
            continue
            
    return None, None, None