#!/usr/bin/env python3
from console_control import install_console_output_override, console_print

install_console_output_override()

import secrets
import socket
import struct
import sys
import threading
import traceback
import time

from BitBuffer import BitBuffer
from PKTTYPES import PACKET_HANDLERS
from PolicyServer import start_policy_server
from constants import Entity
from globals import HOST, PORTS, handle_entity_destroy_server, GS
from scheduler import set_active_session_resolver
from static_server import start_static_server
from accounts import save_characters, load_accounts, load_characters
from level_config import LEVEL_CONFIG


#===========#

ENABLE_ADMIN_PANEL = False
# Keep disabled for normal gameplay flow.
# When enabled, clients connecting on port 7498 may skip character-select/login flow.
ENABLE_MASTER_CLIENT_BOOTSTRAP = False

#===========#

def _level_remove(level, session):
    # Remove from registry
    s = GS.level_registry.get(level)
    if s and session in s:
        s.remove(session)

    # Remove all entities owned by this session from the level
    level_map = GS.level_entities.get(level)
    if not level_map:
        return

    to_remove = [
        eid for eid, ent in level_map.items()
        if ent.get("session") is session
    ]

    for eid in to_remove:
        del level_map[eid]


def _purge_session_entities(session):
    """Best-effort cleanup for ghost entities left by this session across all levels."""
    player_name = getattr(session, "current_character", None)
    player_eid = getattr(session, "clientEntID", None)

    for level_name, level_map in list(GS.level_entities.items()):
        if not isinstance(level_map, dict) or not level_map:
            continue

        stale_ids = []
        for eid, ent in list(level_map.items()):
            if not isinstance(ent, dict):
                continue

            if ent.get("session") is session:
                stale_ids.append(eid)
                continue

            if player_eid is not None and eid == player_eid:
                stale_ids.append(eid)
                continue

            props = ent.get("props") if isinstance(ent.get("props"), dict) else {}
            ent_name = props.get("name")
            if player_name and ent_name == player_name and ent.get("kind") == "player":
                stale_ids.append(eid)

        for eid in stale_ids:
            level_map.pop(eid, None)

    for level_name, sessions in list(GS.level_registry.items()):
        if session in sessions:
            sessions.discard(session)
        if not sessions:
            GS.level_registry.pop(level_name, None)



def new_transfer_token():
    """Allocate a persistent 16-bit token not in use."""
    while True:
        t = secrets.randbits(16)
        if t not in GS.session_by_token and t not in GS.pending_world and t not in GS.used_tokens and t not in GS.token_char:
           return t


def _select_master_boot_character():
    """
    Pick a deterministic character for DEVFLAG_MASTER_CLIENT bootstrap.
    We prefer latest user IDs first and highest-level character within that user.
    """
    try:
        accounts = load_accounts()
    except Exception:
        return None, None

    user_ids = sorted({int(uid) for uid in accounts.values()}, reverse=True)
    for uid in user_ids:
        try:
            chars = load_characters(uid)
        except Exception:
            continue
        if not chars:
            continue
        best = max(
            chars,
            key=lambda c: (
                int(c.get("level", 0) or 0),
                str(c.get("name", "")),
            ),
        )
        return uid, best
    return None, None


def _prepare_master_transfer(char: dict, user_id: int):
    char_name = str(char.get("name", "")).strip()
    if not char_name:
        return None, None, None

    key = (int(user_id), char_name)
    old_tk = GS.char_tokens.get(key)
    if old_tk is not None:
        GS.session_by_token.pop(old_tk, None)
        GS.pending_world.pop(old_tk, None)
        GS.used_tokens.pop(old_tk, None)
        GS.token_char.pop(old_tk, None)

    token = new_transfer_token()
    GS.char_tokens[key] = token
    GS.token_char[token] = key

    target_level = char.get("CurrentLevel", {}).get("name", "CraftTown")
    previous_level = char.get("PreviousLevel", {}).get("name", "NewbieRoad")
    GS.pending_world[token] = (char, target_level, previous_level)
    GS.pending_extended[token] = True
    return token, target_level, previous_level


def _send_master_port_packet(session, host: str, port: int):
    bb = BitBuffer()
    bb.write_method_26(host or HOST)
    bb.write_method_91(max(0, int(port)))
    payload = bb.to_bytes()
    session.conn.sendall(struct.pack(">HH", 0x23, len(payload)) + payload)


def _send_master_start_level_packet(
    session,
    map_id: int,
    level_swf: str,
    internal_name: str,
    map_level: int,
    base_level: int,
    moment_params: str,
    alter_params: str,
    is_instanced: bool,
    monster_bonus_level: int = 0,
):
    bb = BitBuffer()
    bb.write_method_4(int(map_id))
    bb.write_method_26(level_swf or "")
    bb.write_method_26(internal_name or "")
    bb.write_method_6(max(0, int(map_level)), Entity.MAX_CHAR_LEVEL_BITS)
    bb.write_method_6(max(0, int(base_level)), Entity.MAX_CHAR_LEVEL_BITS)
    bb.write_method_4(max(0, int(monster_bonus_level)))
    bb.write_method_26(moment_params or "")
    bb.write_method_26(alter_params or "")
    bb.write_method_15(bool(is_instanced))
    payload = bb.to_bytes()
    session.conn.sendall(struct.pack(">HH", 0x24, len(payload)) + payload)


def _bootstrap_master_client(session):
    """
    DEVFLAG_MASTER_CLIENT bootstrap:
    - Send 0x23 with game host/port.
    - Send 0x24 with a transfer token + initial level so Main can create Game.
    """
    if not ENABLE_MASTER_CLIENT_BOOTSTRAP:
        return

    listen_port = int(getattr(session, "listen_port", 0) or 0)
    if listen_port != 7498:
        return

    route_port = None
    for p in PORTS:
        try:
            pi = int(p)
        except Exception:
            continue
        if pi != listen_port:
            route_port = pi
            break
    if route_port is None:
        route_port = listen_port

    _send_master_port_packet(session, HOST, route_port)

    user_id, char = _select_master_boot_character()
    if not user_id or not char:
        return

    token, target_level, _previous_level = _prepare_master_transfer(char, user_id)
    if not token:
        return
    session.transfer_token = int(token)
    session._master_boot_token = int(token)

    level_swf, map_level, base_level, is_dungeon = LEVEL_CONFIG.get(
        target_level,
        ("LevelsHome.swf/a_Level_Home", 1, 1, True),
    )
    is_hard = str(target_level).endswith("Hard")
    moment = "Hard" if is_hard else ""
    alter = "Hard" if is_hard else ""

    _send_master_start_level_packet(
        session=session,
        map_id=token,
        level_swf=level_swf,
        internal_name=target_level,
        map_level=map_level,
        base_level=base_level,
        moment_params=moment,
        alter_params=alter,
        is_instanced=is_dungeon,
        monster_bonus_level=0,
    )

def find_active_session(user_id, char_name):
    for s in GS.all_sessions:
        if getattr(s, 'user_id', None) == user_id and getattr(s, 'current_character', None) == char_name and s.authenticated:
            return s
    return None

# register resolver
set_active_session_resolver(find_active_session)

class ClientSession:
    def __init__(self, conn, addr, listen_port=None):
        self.conn = conn
        self.addr = addr
        self.listen_port = listen_port
        self.running = True

        # Authentication / account
        self.user_id = None
        self.authenticated = False
        self.char_list = []           # list of characters belonging to this user
        self.current_character = None # name of active character
        self.current_char_dict = None # dict of active character’s data

        # world and  level
        self.current_level = None
        self.entry_level = None
        self.player_spawned = False
        self.clientEntID = None       # entity ID assigned to the player

        #  entity tracking
        self.entities = {}  # authoritative movement cache
        self.transfer_token = None
        self._story_player_idx_by_level = {}  # level_key -> player_abs_index
        self._story_statue_id_cache = {}      # level_key -> {npc_id: story_key}

        # Some clients occasionally send first_login=0 on initial world connect.
        # Track whether we have already sent the one-time extended player data
        # for this TCP session so we can force it once safely.
        self.sent_initial_extended_data = False




    def stop(self):
        self.running = False
        self.close_connection()

    def get_entity(self, entity_id):
        return self.entities.get(entity_id)


    def ensure_token(self, char, target_level=None, previous_level=None):
        key = (self.user_id, char.get("name"))

        # Always rotate transfer token for a fresh world/login transition.
        # Reusing old tokens across reconnects can leak stale pending/session state.
        old_tk = GS.char_tokens.get(key)
        if old_tk is not None:
            GS.session_by_token.pop(old_tk, None)
            GS.pending_world.pop(old_tk, None)
            GS.used_tokens.pop(old_tk, None)
            GS.token_char.pop(old_tk, None)

        tk = new_transfer_token()
        GS.char_tokens[key] = tk
        GS.token_char[tk] = key

        # Store transfer/session mapping (separate from runtime entity id)
        self.transfer_token = tk
        GS.session_by_token[tk] = self

        return tk

    def save_player_position(self):
        if not (self.user_id and self.char_list and self.current_character):
            return

        char = next((c for c in self.char_list if c.get("name") == self.current_character), None)
        if not char:
            return

        current_level = self.current_level
        ent = self.entities.get(self.clientEntID)

        if not (current_level and ent):
            return

        # Determine whether saving is allowed
        is_dungeon = LEVEL_CONFIG.get(current_level, ("", 0, 0, False))[3]
        allow_save = (current_level == "CraftTown") or not is_dungeon

        if not allow_save:
            return

        # ONLY update coords, never the level name here
        char["CurrentLevel"]["x"] = ent.get("pos_x", 0)
        char["CurrentLevel"]["y"] = ent.get("pos_y", 0)

        save_characters(self.user_id, self.char_list)

        #print(
        #    f"[{self.addr}] Saved player position: "
        #    f"{char['CurrentLevel']['name']} → "
        #    f"({char['CurrentLevel']['x']}, {char['CurrentLevel']['y']})"
        #)

    def close_connection(self):

        self.save_player_position()

        if self.player_spawned and self.clientEntID is not None:
            handle_entity_destroy_server(self, self.clientEntID, all_sessions=GS.all_sessions)
            #print("destroyed entity removal")

        # Always remove this session from level tracking, even if spawn did not complete.
        # Otherwise stale pre-login sessions can survive reconnects and create ghost state.
        if self.current_level:
            _level_remove(self.current_level, self)

        # Safety purge: remove any lingering references owned by this session.
        _purge_session_entities(self)

        try:
            self.conn.close()
        except:
            pass

        # Remove token mappings owned by this session.
        stale_tokens = [
            tk for tk, sess in list(GS.session_by_token.items())
            if sess is self
        ]
        for tk in stale_tokens:
            GS.session_by_token.pop(tk, None)

        if self in GS.all_sessions:
            GS.all_sessions.remove(self)

        if self.user_id in GS.current_characters:
            GS.current_characters.pop(self.user_id, None)


def handle_client(session: ClientSession):
    conn = session.conn
    addr = session.addr
    print("Connected:", addr)
    conn.settimeout(300)
    buffer = bytearray()

    # In master-client mode, Main expects 0x23 + 0x24 immediately to create Game.
    try:
        _bootstrap_master_client(session)
    except Exception:
        traceback.print_exc()

    try:
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                print(f"[{addr}] Connection closed by client")
                break
            buffer.extend(chunk)
            while len(buffer) >= 4:
                pkt    = int.from_bytes(buffer[0:2], byteorder='big')
                length = int.from_bytes(buffer[2:4], byteorder='big')
                total  = 4 + length
                if len(buffer) < total:
                    break
                data    = bytes(buffer[:total])
                payload = data[4:]
                del buffer[:total]

                # Sanity check
                if len(payload) != length:
                    print(f"[{addr}] Length mismatch: header says {length} but payload is {len(payload)}")

                handler = PACKET_HANDLERS.get(pkt)

                if handler:
                    handler(session, data)
                else:
                    print(f"[{session.addr}] Unhandled packet type: 0x{pkt:02X}, raw payload = {data.hex()}")

    except socket.timeout:
        print(f"[{addr}] Connection timed out")
    except OSError as e:
        if e.errno == 9:
            print(f"[{addr}] Connection closed")
        else:
            print("Session error:", e)
            traceback.print_exc()
    except Exception as e:
        print("Session error:", e)
        traceback.print_exc()
    finally:
        print("Disconnect:", addr)
        session.stop()

def start_server(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((HOST, port))
    except PermissionError:
        console_print(f"Error: Cannot bind to port {port}. Ports below 1024 require root privileges.")
        return None
    except OSError as e:
        console_print(f"Error: Cannot bind to port {port}. {e}")
        return None
    s.listen(5)
    console_print(f"Server listening on {HOST}:{port}")
    return s

def accept_connections(s, port):
    while True:
        conn, addr = s.accept()
        session = ClientSession(conn, addr, listen_port=port)
        GS.all_sessions.append(session)
        threading.Thread(target=handle_client, args=(session,), daemon=True).start()

def start_servers():
    servers = []
    for port in PORTS:
        server = start_server(port)
        if server:
            servers.append((server, port))
            threading.Thread(target=accept_connections, args=(server, port), daemon=True).start()
    return servers

if __name__ == "__main__":
    start_policy_server(host="127.0.0.1", port=843)
    start_static_server(host="127.0.0.1", port=80, directory="content/localhost")
    servers = start_servers()
    console_print("For Browser running on : http://localhost/index.html")
    console_print("For Flash Projector running on : http://localhost/p/cbv/DungeonBlitz.swf?fv=cbq&gv=cbv")

    if ENABLE_ADMIN_PANEL:
        try:
            from admin_panel import run_admin_panel

            threading.Thread(target=run_admin_panel,args=(lambda: GS.all_sessions, 5000),daemon=True).start()
            console_print("Debug Panel running on http://127.0.0.1:5000/")
        except ModuleNotFoundError:
            console_print(
                """
        ------------------------------------------------------------------------------------------
        Flask is not installed. Admin panel disabled.

        If you want to use the admin panel you need to install Flask:

        Enter this command in the command prompt => pip install flask

        Then restart the server.
        ------------------------------------------------------------------------------------------
                """
            )
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down servers...")
        for server, port in servers:
            server.close()
        sys.exit(0)
