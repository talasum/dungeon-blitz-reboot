import math
import time
import threading
import struct
import os
import re
from BitBuffer import BitBuffer
from globals import GS, send_hp_update, get_npc_props
from combat import apply_and_broadcast_hp_delta
from game_data import get_ent_type

#AI now enabled for server-side enemy control
AI_ENABLED = True

AI_INTERVAL = 0.125
TIMESTEP = 1 / 60.0
MELEE_AGGRO_RADIUS = 320
RANGED_AGGRO_RADIUS = 520
LEASH_RADIUS = 1800
MAX_SPEED = 400.0  # Reduced from 1200 for less sliding
ACCELERATION = 40.0
FRICTION = 0.85     # Increased friction (0-1 multiplier approach or constant subtraction)
STOP_DISTANCE = 50
ATTACK_RANGE = 95
RANGED_ATTACK_RANGE = 300  # Ranged enemies stop and shoot from this distance
ATTACK_COOLDOWN = 1.0  # per-monster attack interval (seconds)
BASE_NPC_DAMAGE = 15  # base damage for NPC attacks
VERTICAL_TOLERANCE = 120  # allowable vertical diff to attack
FLYING_VERTICAL_TOLERANCE = 240
STALL_TIME = 2.0         # seconds before nudging a stuck NPC
STALL_MIN_MOVE = 20       # min distance change to consider progress
STALL_NUDGE_VELOCITY = 220
DEFAULT_MELEE_POWER_ID = 1693  # DefaultMobMelee fallback
DEFAULT_RANGED_POWER_ID = 1694  # DefaultMobFireball fallback
BOSS_SKILL_DEFAULT_COOLDOWN = 7.5

_monster_power_ids = None
_monster_power_catalog = None

PROXY_POWER_ID_MAP = {
    "EyeBolt": 1785,
    "EyeBoltBig": 1786,
    "EyeBoltHard": 1789,
    "EyeBoltBigger": 1787,
    "Fireball": 10,
    "FireballBig": 10,
    "PsychicOrb": 54,
    "AcidSpit": 15,
    "DevourerFireball": 1776,
    "DevourerFireballHard": 1780,
    "DevourerSuperSpit": 1784,
    "BatBolt": 1788,
}

OFFENSIVE_TARGET_METHODS = {
    "Melee",
    "Cleave",
    "Projectile",
    "Blast",
    "Charge",
    "Wave",
    "RangedAoE",
    "PBAoE",
    "Ray",
    "Nova",
}

PROJECTILE_STYLE_TARGET_METHODS = {
    "Projectile",
    "Wave",
    "RangedAoE",
    "Ray",
    "Blast",
}

# ─────────────── Core helpers ───────────────
def get_pos(ent):
    """Get position from entity, checking both x/y and pos_x/pos_y"""
    x = ent.get("pos_x", ent.get("x", 0.0))
    y = ent.get("pos_y", ent.get("y", 0.0))
    return x, y

def distance(a, b):
    ax, ay = get_pos(a)
    bx, by = get_pos(b)
    return math.hypot(ax - bx, ay - by)


def is_flying_enemy(ent_name, ent_type_data):
    name_l = (ent_name or "").lower()
    behavior_l = ((ent_type_data or {}).get("Behavior", "") or "").lower()
    return "fly" in name_l or "ghost" in name_l or "air" in behavior_l


def log_ai_state(npc, state, detail=""):
    prev_state = npc.get("_ai_last_state")
    now = time.monotonic()
    last_logged_at = float(npc.get("_ai_last_state_log_at", 0.0))
    if state != prev_state or (now - last_logged_at) >= 4.0:
        if state == "idle" and prev_state == "idle":
            npc["_ai_last_state_log_at"] = now
            return
        npc_name = npc.get("name", "Unknown")
        npc_id = npc.get("id", 0)
        suffix = f" | {detail}" if detail else ""
        print(f"[AI State] {npc_name}#{npc_id} -> {state}{suffix}")
        npc["_ai_last_state"] = state
        npc["_ai_last_state_log_at"] = now


def _extract_tag_text(block_text, tag_name):
    m = re.search(rf"<{tag_name}>(.*?)</{tag_name}>", block_text)
    if not m:
        return None
    return m.group(1).strip()


def _extract_tag_int(block_text, tag_name):
    text = _extract_tag_text(block_text, tag_name)
    if text is None:
        return None
    m = re.match(r"-?\d+", text)
    if not m:
        return None
    try:
        return int(m.group(0))
    except Exception:
        return None


def load_monster_power_catalog():
    """
    Load monster power metadata from Game.swz dump once.
    Returns:
      {
        power_name: {
            "power_id": int,
            "target_method": str,
            "range": int|None,
            "cooldown_ms": int|None,
        }
      }
    Falls back to an empty mapping if the file is unavailable.
    """
    global _monster_power_catalog
    if _monster_power_catalog is not None:
        return _monster_power_catalog

    _monster_power_catalog = {}
    swz_path = os.path.normpath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "extra-modules",
            "swz-scripts",
            "Game.swz.txt",
        )
    )

    try:
        with open(swz_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        start = text.find("<MonsterPowerTypes")
        end = text.find("</MonsterPowerTypes>")
        if start != -1 and end != -1 and end > start:
            text = text[start:end]

        pattern = re.compile(r'<Power\s+PowerName="([^"]+)">([\s\S]*?)</Power>')
        for power_name, block in pattern.findall(text):
            power_id = _extract_tag_int(block, "PowerID")
            target_method = _extract_tag_text(block, "TargetMethod") or ""
            power_range = _extract_tag_int(block, "Range")
            cooldown_ms = _extract_tag_int(block, "CoolDownTime")
            _monster_power_catalog[power_name] = {
                "power_id": power_id or 0,
                "target_method": target_method,
                "range": power_range,
                "cooldown_ms": cooldown_ms,
            }

        print(f"[AI Attack] Loaded {len(_monster_power_catalog)} monster power definitions from Game.swz.txt")
    except Exception as e:
        print(f"[AI Attack] Could not load monster power catalog: {e}")

    return _monster_power_catalog


def load_monster_power_ids():
    """
    Backward-compatible helper for name -> power_id mapping.
    """
    global _monster_power_ids
    if _monster_power_ids is not None:
        return _monster_power_ids

    catalog = load_monster_power_catalog()
    _monster_power_ids = {
        power_name: int(meta.get("power_id", 0))
        for power_name, meta in catalog.items()
        if int(meta.get("power_id", 0)) > 0
    }
    return _monster_power_ids


def resolve_npc_power(ent_type_data, force_melee=False):
    """
    Resolve attack power for NPC cast animation.
    Returns (power_name, power_id, has_projectile).
    """
    melee_power_name = (ent_type_data or {}).get("MeleePower", "") or ""
    ranged_power_name = (ent_type_data or {}).get("RangedPower", "") or ""
    if force_melee:
        selected_power_name = melee_power_name or ranged_power_name
    else:
        selected_power_name = ranged_power_name or melee_power_name
    has_projectile = bool(ranged_power_name and selected_power_name == ranged_power_name)

    if not selected_power_name:
        return "DefaultMobMelee", DEFAULT_MELEE_POWER_ID, False

    power_id_map = load_monster_power_ids()
    power_id = power_id_map.get(selected_power_name, 0)
    if power_id:
        return selected_power_name, power_id, has_projectile

    proxy_id = PROXY_POWER_ID_MAP.get(selected_power_name)
    if proxy_id:
        return selected_power_name, proxy_id, has_projectile

    if has_projectile:
        return selected_power_name, DEFAULT_RANGED_POWER_ID, True
    return selected_power_name, DEFAULT_MELEE_POWER_ID, False


def resolve_boss_skill(ent_type_data):
    """
    Resolve the first offensive boss skill from EntTypes.Powers.
    Returns:
      {
        "power_name": str,
        "power_id": int,
        "has_projectile": bool,
        "target_method": str,
        "range": float,
        "cooldown": float,
      }
    or None for non-boss/unusable data.
    """
    if not ent_type_data or ent_type_data.get("EntRank") != "Boss":
        return None

    powers_raw = (ent_type_data.get("Powers", "") or "").strip()
    if not powers_raw or powers_raw.lower() == "none":
        return None

    catalog = load_monster_power_catalog()
    for power_name in [p.strip() for p in powers_raw.split(",") if p.strip()]:
        meta = catalog.get(power_name, {})
        target_method = (meta.get("target_method", "") or "").strip()
        if target_method not in OFFENSIVE_TARGET_METHODS:
            continue

        power_id = int(meta.get("power_id", 0) or 0)
        if not power_id:
            power_id = int(load_monster_power_ids().get(power_name, 0))
        if not power_id:
            power_id = int(PROXY_POWER_ID_MAP.get(power_name, 0))
        if not power_id:
            continue

        skill_range = meta.get("range")
        if isinstance(skill_range, int) and skill_range > 0:
            effective_range = float(skill_range)
        elif target_method in PROJECTILE_STYLE_TARGET_METHODS:
            effective_range = float(RANGED_ATTACK_RANGE)
        else:
            effective_range = float(ATTACK_RANGE)

        cooldown_ms = meta.get("cooldown_ms")
        if isinstance(cooldown_ms, int) and cooldown_ms > 0:
            cooldown_sec = cooldown_ms / 1000.0
        else:
            cooldown_sec = BOSS_SKILL_DEFAULT_COOLDOWN

        return {
            "power_name": power_name,
            "power_id": power_id,
            "has_projectile": target_method in PROJECTILE_STYLE_TARGET_METHODS,
            "target_method": target_method,
            "range": effective_range,
            "cooldown": cooldown_sec,
        }

    return None

def update_npc_physics(npc, dt=TIMESTEP, steps=18):
    vx = npc.get("velocity_x", 0.0)
    vy = npc.get("velocity_y", 0.0)
    
    # Simple friction/damping
    vx *= FRICTION
    vy *= FRICTION
    
    # Stop if very slow
    if abs(vx) < 1.0: vx = 0
    if abs(vy) < 1.0: vy = 0

    npc["pos_x"] += vx * dt * steps
    npc["pos_y"] += vy * dt * steps
    npc["x"] = npc["pos_x"]
    npc["y"] = npc["pos_y"]
    npc["velocity_x"] = vx
    npc["velocity_y"] = vy

def broadcast_npc_move(npc, level_name, delta_x, delta_y, delta_vx):
    recipients = [s for s in GS.all_sessions if s.player_spawned and s.current_level == level_name]

    bb = BitBuffer()
    bb.write_method_4(npc["id"])
    bb.write_method_45(int(delta_x))
    bb.write_method_45(int(delta_y))
    bb.write_method_45(int(delta_vx))
    bb.write_method_6(int(npc.get("entState", 0)), 2)
    bb.write_method_15(npc.get("b_left", False))
    bb.write_method_15(npc.get("b_running", False))
    bb.write_method_15(npc.get("b_jumping", False))
    bb.write_method_15(npc.get("b_dropping", False))
    bb.write_method_15(npc.get("b_backpedal", False))
    bb.write_method_15(False)  # is_airborne; server AI currently doesn't use airborne velocity

    payload = bb.to_bytes()
    pkt = struct.pack(">HH", 0x07, len(payload)) + payload

    for s in recipients:
        try:
            s.conn.sendall(pkt)
        except Exception as e:
            print(f"    ✗ {s.addr}: {e}")


def broadcast_remove_buff(entity_id, buff_type_id, instance_id, level_name):
    recipients = [s for s in GS.all_sessions if s.player_spawned and s.current_level == level_name]
    
    bb = BitBuffer(debug=False)
    bb.write_method_9(entity_id)
    bb.write_method_9(buff_type_id)
    bb.write_method_9(instance_id)
    payload = bb.to_bytes()
    pkt = struct.pack(">HH", 0x0C, len(payload)) + payload

    for s in recipients:
        try:
            s.conn.sendall(pkt)
        except Exception as e:
            print(f"[AI Buff] Error sending buff remove to {s.addr}: {e}")

def broadcast_npc_attack(
    npc,
    target_player,
    level_name,
    damage,
    selected_power=None,
    attack_kind="basic",
    skill_cooldown_left=0.0,
):
    """Broadcast NPC attack: power cast + power hit packets."""
    recipients = [s for s in GS.all_sessions if s.player_spawned and s.current_level == level_name]
    
    npc_id = npc["id"]
    target_id = target_player.get("id")
    if selected_power:
        power_name = selected_power.get("power_name", "DefaultMobMelee")
        power_id = int(selected_power.get("power_id", DEFAULT_MELEE_POWER_ID))
        has_projectile = bool(selected_power.get("has_projectile", False))
    else:
        ent_type_data = get_ent_type(npc.get("name", ""))
        power_name, power_id, has_projectile = resolve_npc_power(ent_type_data)

    print(
        f"[AI Attack] kind:{attack_kind} NPC ID:{npc_id} targeting Player ID:{target_id}, "
        f"damage:{damage}, power:{power_name}({power_id}), projectile:{has_projectile}, "
        f"skill_cd_left:{max(0.0, float(skill_cooldown_left)):.2f}s"
    )
    
    # Build power cast packet (0x09)
    bb_cast = BitBuffer(debug=False)
    bb_cast.write_method_4(npc_id)
    bb_cast.write_method_4(power_id)
    bb_cast.write_method_15(bool(target_id))  # has_target_entity
    bb_cast.write_method_15(has_projectile)   # has_target_pos
    if has_projectile:
        tx, ty = get_pos(target_player)
        bb_cast.write_method_45(int(tx))
        bb_cast.write_method_45(int(ty))
    bb_cast.write_method_15(has_projectile)   # has_projectile
    if has_projectile:
        projectile_id = ((npc_id & 0xFFFF) << 12) | (int(time.time() * 1000) & 0xFFF)
        bb_cast.write_method_4(projectile_id)
    bb_cast.write_method_15(False)  # is_charged
    bb_cast.write_method_15(False)  # has_extra
    bb_cast.write_method_15(False)  # has_flags
    
    cast_payload = bb_cast.to_bytes()
    cast_pkt = struct.pack(">HH", 0x09, len(cast_payload)) + cast_payload
    
    # Build power hit packet (0x0A) — only used for non-projectile (melee) attacks.
    # For projectile powers, the client expects the hit after projectile impact,
    # so we skip 0x0A and rely on the 0x3A authoritative HP update instead.
    hit_pkt = None
    if not has_projectile:
        bb_hit = BitBuffer(debug=False)
        bb_hit.write_method_4(target_id)
        bb_hit.write_method_4(npc_id)
        bb_hit.write_method_24(damage)
        bb_hit.write_method_4(power_id)
        
        bb_hit.write_method_15(False)   # has_animation_override
        bb_hit.write_method_15(False)   # has_effect_override
        bb_hit.write_method_15(False)   # is_critical
        
        hit_payload = bb_hit.to_bytes()
        hit_pkt = struct.pack(">HH", 0x0A, len(hit_payload)) + hit_payload
    
    pkt_desc = "cast+hit" if hit_pkt else "cast only (projectile, damage via 0x3A)"
    print(f"[AI Attack] Sending {pkt_desc} for power:{power_name}({power_id}), projectile:{has_projectile}")
    
    # Send to all clients
    for s in recipients:
        try:
            s.conn.sendall(cast_pkt)
            if hit_pkt:
                s.conn.sendall(hit_pkt)
        except Exception as e:
            print(f"[AI Attack] Error sending to {s.addr}: {e}")
            
    # FORCE DAMAGE UPDATE (Server-side authoritative)
    # FORCE DAMAGE UPDATE (Server-side authoritative)
    if damage > 0 and target_id:
        if "session" in target_player:
            try:
                t_session = target_player["session"]
                # Update HP in entity
                current_hp = target_player.get("hp", 100)
                new_hp = max(0, current_hp - damage)
                target_player["hp"] = new_hp
                
                # Also update the session's entity copy if different
                if t_session and t_session.entities.get(target_id):
                    t_session.entities[target_id]["hp"] = new_hp

                print(f"[AI Attack] Hit! Applying {damage} dmg to Player {target_id}. HP: {current_hp} -> {new_hp}")
                
                # Send 0x3A Health Update
                apply_and_broadcast_hp_delta(
                    source_session=target_player["session"],
                    ent_id=target_id,
                    delta=-damage,
                    all_sessions=GS.all_sessions,
                    source_name="NPC_Attack"
                )
                # Also notify the target's own client
                send_hp_update(t_session, target_id, -damage)
            except Exception as e:
                print(f"[AI Attack] Exception during damage apply: {e}")
        else:
            print(f"[AI Attack] Warning: target_player {target_id} has no 'session' key. Damage skipped.")
    else:
        print(f"[AI Attack] Damage skipped: damage={damage}, target_id={target_id}")


# ───────────────── AI loop per level ─────────────────
def run_ai_loop(level_name):
    """Threaded loop driving NPC AI + physics for one level."""
    print(f"[AI] Starting AI loop for level: {level_name}")

    while True:
        time.sleep(AI_INTERVAL)

        current_time = time.time()
        current_mono = time.monotonic()

        level_map = GS.level_entities.get(level_name, {})

        npcs = [
            ent["props"]
            for ent in level_map.values()
            if ent["kind"] == "npc" and ent["props"].get("team", 0) == 2  # Only team 2 enemies
        ]

        # Get players directly from sessions (more reliable than level_entities)
        players = []
        for session in GS.all_sessions:
            if session.player_spawned and session.current_level == level_name and session.clientEntID:
                # Get player entity from session's entities dict
                player_ent = session.entities.get(session.clientEntID)
                if player_ent:
                    px = player_ent.get("pos_x", player_ent.get("x", 0))
                    py = player_ent.get("pos_y", player_ent.get("y", 0))
                    players.append({
                        "id": session.clientEntID,
                        "x": px,
                        "y": py,
                        "pos_x": px,
                        "pos_y": py,
                        "dead": player_ent.get("dead", False),
                        "hp": player_ent.get("hp", 100),
                        "session": session
                    })

        if not npcs or not players:
            continue

        # Debug: Log first iteration per level
        log_key = f'_logged_{level_name}'
        if not hasattr(run_ai_loop, log_key):
            print(f"[AI] Found {len(npcs)} NPCs and {len(players)} players in {level_name}")
            if npcs:
                npc = npcs[0]
                print(f"[AI] Sample NPC: id={npc.get('id')}, name={npc.get('name')}, x={npc.get('x')}, y={npc.get('y')}")
            if players:
                player = players[0]
                print(f"[AI] Sample Player: id={player.get('id')}, x={player.get('x')}, y={player.get('y')}")
            setattr(run_ai_loop, log_key, True)

        # Debug counters
        active_attackers = 0

        for npc in npcs:
            # Skip dead NPCs
            if npc.get("hp", 1) <= 0 or npc.get("dead", False):
                continue
            # Client-spawned entities are controlled by SWF logic, not server AI.
            if npc.get("client_spawned", False):
                continue

            # Skip TreasureChest and stationary/non-combat entities from AI loop
            ent_name = npc.get("name", "")
            ent_type_data = get_ent_type(ent_name) if ent_name else None
            ent_name_l = ent_name.lower() if ent_name else ""
            if "treasurechest" in ent_name_l:
                continue
            if ent_type_data:
                behavior = ent_type_data.get("Behavior", "")
                ent_speed = float(ent_type_data.get("Speed", "10"))
                # Skip treasure chests, stationary entities, and cannon-type entities
                # These are client-side AI entities that shouldn't be server-driven
                if behavior in ("TreasureChest", "GoblinCannon", "NPC", "NPCDummy") or ent_speed <= 0:
                    continue
            
            # Expire buffs for server NPCs
            buffs = npc.setdefault("buffs", [])
            if buffs:
                remaining_buffs = []
                for buff in buffs:
                    if buff.get("expires_at", 0) <= current_time:
                        broadcast_remove_buff(npc["id"], buff.get("buff_type_id", 0), buff.get("instance_id", 0), level_name)
                    else:
                        remaining_buffs.append(buff)
                if len(remaining_buffs) != len(buffs):
                    npc["buffs"] = remaining_buffs

            npc["pos_x"] = npc.get("pos_x", npc.get("x", 0.0))
            npc["pos_y"] = npc.get("pos_y", npc.get("y", 0.0))

            # Find nearest player (track dx, dy)
            closest, closest_dist = None, float("inf")
            closest_dx = closest_dy = 0
            is_ranged = bool(ent_type_data and ent_type_data.get("RangedPower"))
            is_boss = bool(ent_type_data and ent_type_data.get("EntRank") == "Boss")
            if is_boss:
                if npc.get("_boss_skill_cached_for") != ent_name:
                    npc["_boss_skill_data"] = resolve_boss_skill(ent_type_data)
                    npc["_boss_skill_cached_for"] = ent_name
                boss_skill = npc.get("_boss_skill_data")
            else:
                boss_skill = None
                npc.pop("_boss_skill_data", None)
                npc.pop("_boss_skill_cached_for", None)
            aggro_radius = RANGED_AGGRO_RADIUS if is_ranged else MELEE_AGGRO_RADIUS

            # Keep chasing the current target once aggroed (up to leash distance).
            aggro_target_id = npc.get("aggro_target_id")
            if aggro_target_id:
                target = next(
                    (
                        p for p in players
                        if p.get("id") == aggro_target_id and not p.get("dead", False)
                    ),
                    None,
                )
                if target:
                    dx = target.get("pos_x", target.get("x", 0)) - npc["pos_x"]
                    dy = target.get("pos_y", target.get("y", 0)) - npc["pos_y"]
                    d = math.hypot(dx, dy)
                    if d <= LEASH_RADIUS:
                        closest, closest_dist = target, d
                        closest_dx, closest_dy = dx, dy
                    else:
                        npc.pop("aggro_target_id", None)
                else:
                    npc.pop("aggro_target_id", None)

            # Acquire a new target only when a player is actually nearby.
            if not closest:
                for p in players:
                    # Do not gate aggro by hp because player-death state is not always
                    # synchronized as a strict hp<=0 transition in this server flow.
                    if p.get("dead", False):
                        continue
                    dx = p.get("pos_x", p.get("x", 0)) - npc["pos_x"]
                    dy = p.get("pos_y", p.get("y", 0)) - npc["pos_y"]
                    d = math.hypot(dx, dy)
                    if d <= aggro_radius and d < closest_dist:
                        closest, closest_dist = p, d
                        closest_dx, closest_dy = dx, dy

                if closest:
                    npc["aggro_target_id"] = closest["id"]

            # Save last position for delta calc
            last_x = npc.get("var_959", npc["pos_x"])
            last_y = npc.get("var_874", npc["pos_y"])
            last_vx = npc.get("var_1258", 0)

            if closest:
                abs_dx = abs(closest_dx)
                abs_dy = abs(closest_dy)

                vertical_tolerance = FLYING_VERTICAL_TOLERANCE if is_flying_enemy(ent_name, ent_type_data) else VERTICAL_TOLERANCE
                basic_attack_range = ATTACK_RANGE if is_boss else (RANGED_ATTACK_RANGE if is_ranged else ATTACK_RANGE)
                in_basic_attack_range = closest_dist <= basic_attack_range and abs_dy <= vertical_tolerance

                in_skill_attack_range = False
                skill_ready = False
                skill_cooldown_left = 0.0
                if boss_skill:
                    skill_attack_range = float(boss_skill.get("range", ATTACK_RANGE))
                    in_skill_attack_range = closest_dist <= skill_attack_range and abs_dy <= vertical_tolerance
                    next_skill_at = float(npc.get("next_skill_at", 0.0))
                    if next_skill_at - current_mono > 60.0:
                        next_skill_at = 0.0
                        npc["next_skill_at"] = 0.0
                    skill_cooldown_left = max(0.0, next_skill_at - current_mono)
                    skill_ready = current_mono >= next_skill_at

                # Bosses can attack from skill range only if the skill is ready.
                in_attack_window = in_basic_attack_range or (in_skill_attack_range and skill_ready)
                in_aggro_attack_window = closest_dist <= aggro_radius
                can_attack = in_attack_window or in_aggro_attack_window

                # Per-monster cooldown (1 second gap) to avoid burst/stall behavior.
                if can_attack:
                    next_attack_at = float(npc.get("next_attack_at", 0.0))
                    if next_attack_at - current_mono > 10.0:
                        next_attack_at = 0.0
                    if current_mono >= next_attack_at:
                        attack_kind = "basic"
                        selected_power = None
                        if boss_skill and in_skill_attack_range and skill_ready:
                            attack_kind = "skill"
                            selected_power = {
                                "power_name": boss_skill["power_name"],
                                "power_id": boss_skill["power_id"],
                                "has_projectile": boss_skill["has_projectile"],
                            }
                            npc["next_skill_at"] = current_mono + float(boss_skill.get("cooldown", BOSS_SKILL_DEFAULT_COOLDOWN))
                            skill_cooldown_left = 0.0
                        elif is_boss:
                            power_name, power_id, has_projectile = resolve_npc_power(ent_type_data, force_melee=True)
                            selected_power = {
                                "power_name": power_name,
                                "power_id": power_id,
                                "has_projectile": has_projectile,
                            }

                        npc["next_attack_at"] = current_mono + ATTACK_COOLDOWN
                        active_attackers += 1
                        # Calculate damage based on NPC level
                        npc_level = npc.get("level", 1)
                        damage = BASE_NPC_DAMAGE + (npc_level * 2)
                        
                        npc_name = npc.get('name', npc.get('id'))
                        has_no_jump = npc.get("noJumpAttack", False)
                        power_label = selected_power.get("power_name", "auto") if selected_power else "auto"
                        print(
                            f"[AI] {npc_name} attack_kind={attack_kind} power={power_label} "
                            f"dist={closest_dist:.1f}, dx={abs_dx:.1f}, dy={abs_dy:.1f}, "
                            f"aggro_attack={in_aggro_attack_window}, skill_cd_left={skill_cooldown_left:.2f}s | noJumpAttack={has_no_jump}"
                        )
                        broadcast_npc_attack(
                            npc,
                            closest,
                            level_name,
                            damage,
                            selected_power=selected_power,
                            attack_kind=attack_kind,
                            skill_cooldown_left=skill_cooldown_left,
                        )

                # In attack range - stop and attack
                if in_attack_window:
                    npc["pos_y"] = closest.get("pos_y", closest.get("y", npc["pos_y"]))
                    npc["y"] = npc["pos_y"]
                    npc["b_running"] = False
                    npc["b_jumping"] = False
                    npc["b_dropping"] = False
                    npc["b_backpedal"] = False
                    npc["velocity_x"] = 0
                    npc["velocity_y"] = 0
                    npc["b_left"] = closest["pos_x"] < npc["pos_x"] if "pos_x" in closest else closest.get("x", 0) < npc["pos_x"]
                    npc["brain_state"] = "attacking"
                    log_ai_state(
                        npc,
                        "attacking",
                        f"dist={closest_dist:.1f}, dy={abs_dy:.1f}, basic={in_basic_attack_range}, "
                        f"skill={in_skill_attack_range}, skill_ready={skill_ready}, cd={ATTACK_COOLDOWN:.2f}s",
                    )

                    broadcast_npc_move(npc, level_name, 0, 0, 0)
                    continue

                # In aggro range but not attack range - chase
                else:
                    npc["b_running"] = True
                    npc["b_jumping"] = False
                    npc["b_dropping"] = False
                    npc["b_backpedal"] = False
                    cx = closest.get("pos_x", closest.get("x", 0))
                    cy = closest.get("pos_y", closest.get("y", 0))
                    
                    dx = cx - npc["pos_x"]
                    dy = cy - npc["pos_y"]
                    
                    # Normalize and apply speed
                    dist = math.hypot(dx, dy)
                    if dist > 0:
                        ent_speed = float((ent_type_data or {}).get("Speed", 9.0))
                        speed = max(160.0, min(MAX_SPEED, ent_speed * 45.0))
                        if dist < STOP_DISTANCE:
                            speed = speed * (dist / STOP_DISTANCE)
                        
                        vy_boost = 1.5 if abs_dy > vertical_tolerance else 1.0
                        npc["velocity_x"] = (dx / dist) * speed
                        npc["velocity_y"] = (dy / dist) * speed * vy_boost
                    else:
                        npc["velocity_x"] = 0
                        npc["velocity_y"] = 0
                    
                    npc["b_left"] = dx < 0
                    npc["brain_state"] = "chasing"
                    log_ai_state(npc, "chasing", f"dist={closest_dist:.1f}, aggro={aggro_radius}")
            else:
                npc["b_running"] = False
                npc["b_jumping"] = False
                npc["b_dropping"] = False
                npc["b_backpedal"] = False
                npc["velocity_x"] = 0
                npc["velocity_y"] = 0
                npc["brain_state"] = "idle"
                npc.pop("aggro_target_id", None)
                log_ai_state(npc, "idle")

            # Stuck watchdog: if chasing and not making progress, nudge toward player
            if npc.get("brain_state") == "chasing" and closest:
                last_progress_time = npc.get("_last_progress_time", current_time)
                last_progress_pos = npc.get("_last_progress_pos", (npc["pos_x"], npc["pos_y"]))
                moved = math.hypot(npc["pos_x"] - last_progress_pos[0], npc["pos_y"] - last_progress_pos[1])
                if moved >= STALL_MIN_MOVE:
                    npc["_last_progress_time"] = current_time
                    npc["_last_progress_pos"] = (npc["pos_x"], npc["pos_y"])
                elif current_time - last_progress_time > STALL_TIME and closest_dist <= LEASH_RADIUS:
                    # Velocity nudge only; avoid teleporting enemies near the player.
                    npc["velocity_x"] = STALL_NUDGE_VELOCITY if closest_dx > 0 else -STALL_NUDGE_VELOCITY
                    npc["velocity_y"] = max(-STALL_NUDGE_VELOCITY, min(STALL_NUDGE_VELOCITY, closest_dy))
                    npc["_last_progress_time"] = current_time
                    npc["_last_progress_pos"] = (npc["pos_x"], npc["pos_y"])

            update_npc_physics(npc, steps=int(AI_INTERVAL / TIMESTEP))

            # Compute new deltas for packet
            delta_x = int(npc["pos_x"] - last_x)
            delta_y = int(npc["pos_y"] - last_y)
            delta_vx = int(npc["velocity_x"] - last_vx)

            npc["var_959"] = npc["pos_x"]
            npc["var_874"] = npc["pos_y"]
            npc["var_1258"] = npc["velocity_x"]

            if delta_x or delta_y or delta_vx:
                broadcast_npc_move(npc, level_name, delta_x, delta_y, delta_vx)

        # Low activity logging disabled to reduce spam
        # total_hostile = len(npcs)
        # if total_hostile > 0:
        #     activity_ratio = active_attackers / total_hostile
        #     if activity_ratio < 0.1:
        #         print(f"[AI] Low activity: {active_attackers}/{total_hostile} attackers active in {level_name}")

# ─────────────── Thread management ───────────────

_active_ai_threads = {}

def ensure_ai_loop(level_name, run_func=run_ai_loop):
    """Start one AI thread per level (safe to call repeatedly)."""
    if not level_name or level_name in _active_ai_threads:
        return
    t = threading.Thread(target=run_func, args=(level_name,), daemon=True)
    t.start()
    _active_ai_threads[level_name] = t
    print(f"[AI] Started NPC AI thread for level '{level_name}'")
