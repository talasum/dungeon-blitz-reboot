#!/usr/bin/env python3
"""
Patch DungeonBlitz.swf for client-side AI (cue spawning for all levels).

Two patches:
  1. Set DevSettings.flags = 32 (DEVFLAG_SPAWN_MONSTERS)
  2. In Level.method_1003(): Remove the var_333 (Home-only) check
     so cues spawn for ALL levels, not just Home.
     
     Original:  if(!const_919) { if(this.var_333) { SpawnCue... } return; }
     Patched:   if(!const_919) { SpawnCue for all rooms... return; }
     
     Bytecode: iffalse (0x12 + s24) → pop + nop + nop + nop
     Stack-safe: pop removes the boolean just like iffalse would.
"""

import struct, zlib, sys, os, shutil

TARGET_FLAGS = 32  # DEVFLAG_SPAWN_MONSTERS only (safe for init)

# AVM2 opcode table for disassembly
OPCODE_INFO = {}

def _init_opcodes():
    NO = []
    U30 = ['u30']; S24 = ['s24']; U30U30 = ['u30','u30']
    for op in [0x01,0x02,0x03,0x07,0x09,0x1C,0x1D,0x1E,0x1F,
               0x20,0x21,0x23,0x26,0x27,0x28,0x29,0x2A,0x2B,0x30,
               0x35,0x36,0x37,0x38,0x39,0x3A,0x3B,0x3C,0x3D,0x3E,
               0x47,0x48,0x50,0x51,0x52,0x57,
               0x64,0x70,0x71,0x72,0x73,0x74,0x75,0x76,0x77,0x78,
               0x81,0x82,0x83,0x84,0x85,0x87,0x88,0x89,
               0x90,0x91,0x93,0x95,0x96,0x97,
               0xA0,0xA1,0xA2,0xA3,0xA4,0xA5,0xA6,0xA7,
               0xA8,0xA9,0xAA,0xAB,0xAC,0xAD,0xAE,0xAF,
               0xB0,0xB1,0xB3,0xB4,
               0xC0,0xC1,0xC4,0xC5,0xC6,0xC7,
               0xD0,0xD1,0xD2,0xD3,0xD4,0xD5,0xD6,0xD7]:
        OPCODE_INFO[op] = NO
    for op in [0x04,0x05,0x06,0x08,0x25,0x2C,0x2D,0x2E,0x2F,0x31,
               0x40,0x41,0x42,0x49,0x53,0x55,0x56,0x58,0x59,0x5A,
               0x5D,0x5E,0x5F,0x60,0x61,0x62,0x63,0x65,0x66,
               0x68,0x6A,0x6C,0x6D,0x6E,0x6F,
               0x80,0x86,0x92,0x94,0xB2,
               0xC2,0xC3,0xF0,0xF1,0xF2]:
        OPCODE_INFO[op] = U30
    for op in [0x0C,0x0D,0x0E,0x0F,0x10,0x11,0x12,
               0x13,0x14,0x15,0x16,0x17,0x18,0x19,0x1A]:
        OPCODE_INFO[op] = S24
    for op in [0x43,0x44,0x45,0x46,0x4A,0x4C,0x4E,0x4F]:
        OPCODE_INFO[op] = U30U30
    OPCODE_INFO[0x24] = ['s8']
    OPCODE_INFO[0x32] = ['u30','u30']
    OPCODE_INFO[0xEF] = ['debug']
    OPCODE_INFO[0x1B] = ['lookupswitch']

_init_opcodes()

OPCODE_NAMES = {
    0x02:'nop',0x03:'throw',0x08:'kill',0x09:'label',
    0x10:'jump',0x11:'iftrue',0x12:'iffalse',
    0x24:'pushbyte',0x26:'pushtrue',0x27:'pushfalse',
    0x29:'pop',0x2A:'dup',0x2B:'swap',
    0x30:'pushscope',0x47:'returnvoid',0x48:'returnvalue',
    0x60:'getlex',0x62:'getlocal',0x66:'getproperty',0x61:'setproperty',
    0x76:'convert_b',0x82:'coerce_a',0x96:'not',
    0xA8:'bitand',0xA9:'bitor',
    0xD0:'getlocal_0',0xD1:'getlocal_1',0xD2:'getlocal_2',0xD3:'getlocal_3',
}


def read_u30(d, p):
    r = 0; s = 0
    for _ in range(5):
        b = d[p]; p += 1; r |= (b & 0x7F) << s; s += 7
        if not (b & 0x80): break
    return r, p

def write_u30(v):
    r = bytearray()
    while True:
        b = v & 0x7F; v >>= 7
        if v: b |= 0x80
        r.append(b)
        if not v: break
    return bytes(r)

def read_s32(d, p):
    r = 0; s = 0; b = 0
    for _ in range(5):
        b = d[p]; p += 1; r |= (b & 0x7F) << s; s += 7
        if not (b & 0x80): break
    if s < 32 and (b & 0x40): r |= -(1 << s)
    return r, p

def read_s24(d, p):
    v = d[p] | (d[p+1] << 8) | (d[p+2] << 16)
    if v & 0x800000: v -= 0x1000000
    return v, p + 3


def skip_trait(d, p):
    """Skip over a single trait entry."""
    _, p = read_u30(d, p)
    kind = d[p]; p += 1
    kind_id = kind & 0x0F
    attrs = kind >> 4
    if kind_id in (0, 6):
        _, p = read_u30(d, p)
        _, p = read_u30(d, p)
        vi, p = read_u30(d, p)
        if vi: p += 1
    elif kind_id in (1, 2, 3):
        _, p = read_u30(d, p)
        _, p = read_u30(d, p)
    elif kind_id == 4:
        _, p = read_u30(d, p)
        _, p = read_u30(d, p)
    elif kind_id == 5:
        _, p = read_u30(d, p)
        _, p = read_u30(d, p)
    if attrs & 0x04:
        mc, p = read_u30(d, p)
        for _ in range(mc): _, p = read_u30(d, p)
    return p


def read_trait_info(d, p, mn_map):
    """Read a trait, return (name_str, kind_id, method_idx, end_pos)."""
    name_idx, p = read_u30(d, p)
    name = mn_map.get(name_idx, f'#{name_idx}')
    kind = d[p]; p += 1
    kind_id = kind & 0x0F
    attrs = kind >> 4
    method_idx = None
    if kind_id in (0, 6):
        _, p = read_u30(d, p)
        _, p = read_u30(d, p)
        vi, p = read_u30(d, p)
        if vi: p += 1
    elif kind_id in (1, 2, 3):
        _, p = read_u30(d, p)
        method_idx, p = read_u30(d, p)
    elif kind_id == 4:
        _, p = read_u30(d, p)
        _, p = read_u30(d, p)
    elif kind_id == 5:
        _, p = read_u30(d, p)
        _, p = read_u30(d, p)
    if attrs & 0x04:
        mc, p = read_u30(d, p)
        for _ in range(mc): _, p = read_u30(d, p)
    return name, kind_id, method_idx, p


def disassemble(code):
    instrs = []
    pos = 0
    while pos < len(code):
        start = pos
        op = code[pos]; pos += 1
        ops = []
        info = OPCODE_INFO.get(op)
        if info is None:
            instrs.append((start, op, [])); continue
        for ot in info:
            if ot == 'u30':
                v, pos = read_u30(code, pos); ops.append(('u30', v))
            elif ot == 's24':
                v, pos = read_s24(code, pos); ops.append(('s24', v))
            elif ot == 's8':
                v = code[pos]
                if v > 127: v -= 256
                pos += 1; ops.append(('s8', v))
            elif ot == 'debug':
                dt = code[pos]; pos += 1; ops.append(('u8', dt))
                idx, pos = read_u30(code, pos); ops.append(('u30', idx))
                reg = code[pos]; pos += 1; ops.append(('u8', reg))
                ex, pos = read_u30(code, pos); ops.append(('u30', ex))
            elif ot == 'lookupswitch':
                do, pos = read_s24(code, pos); ops.append(('s24', do))
                cc, pos = read_u30(code, pos); ops.append(('u30', cc))
                for _ in range(cc + 1):
                    co, pos = read_s24(code, pos); ops.append(('s24', co))
        instrs.append((start, op, ops))
    return instrs


def main():
    swf_path = "content/localhost/p/cbv/DungeonBlitz.swf"
    bak = swf_path + ".bak"
    if not os.path.exists(bak):
        shutil.copy2(swf_path, bak)
        print("Backed up")

    with open(swf_path, 'rb') as f:
        raw = f.read()

    sig = raw[:3].decode('ascii'); ver = raw[3]
    print(f"SWF: {sig} v{ver}")

    if sig == 'CWS':
        body = bytearray(zlib.decompress(raw[8:]))
    elif sig == 'FWS':
        body = bytearray(raw[8:])
    else:
        print("Bad sig"); sys.exit(1)

    pos = 0
    nb = body[0] >> 3
    pos = (5 + nb * 4 + 7) // 8 + 4

    while pos < len(body):
        tc = struct.unpack_from('<H', body, pos)[0]; pos += 2
        tt = tc >> 6; tl = tc & 0x3F
        is_long = (tl == 0x3F); tl_pos = pos
        if is_long:
            tl = struct.unpack_from('<I', body, pos)[0]; pos += 4
        tds = pos

        if tt == 82:
            ao = tds + 4
            while body[ao] != 0: ao += 1
            ao += 1
            print(f"DoABC2 at {tds}, ABC at {ao}")
            result = patch_abc(body, ao)
            if result:
                sd = result.get('size_delta', 0)
                if sd and is_long:
                    struct.pack_into('<I', body, tl_pos, tl + sd)
                    print(f"  Tag length: {tl} -> {tl + sd}")
                nfl = 8 + len(body)
                with open(swf_path, 'wb') as f:
                    f.write(sig.encode('ascii'))
                    f.write(bytes([ver]))
                    f.write(struct.pack('<I', nfl))
                    if sig == 'CWS':
                        f.write(zlib.compress(bytes(body)))
                    else:
                        f.write(bytes(body))
                print(f"\n✓ Patched: {swf_path} ({os.path.getsize(swf_path)} bytes)")
                return
            else:
                print("FAIL"); sys.exit(1)

        pos = tds + tl

    print("No DoABC2!"); sys.exit(1)


def patch_abc(body, abc_start):
    p = abc_start + 4

    # Int pool
    ic, p = read_u30(body, p)
    for _ in range(1, ic): _, p = read_s32(body, p)

    # UInt pool
    ucp = p
    uc, p = read_u30(body, p)
    for _ in range(1, uc): _, p = read_u30(body, p)
    print(f"  uint_count={uc} at {ucp}")

    # Double pool
    dc, p = read_u30(body, p)
    for _ in range(1, dc): p += 8

    # String pool
    sc, p = read_u30(body, p)
    sp = [""]
    for i in range(1, sc):
        sl, p = read_u30(body, p)
        sp.append(body[p:p+sl].decode('utf-8', errors='replace'))
        p += sl

    # Namespace pool
    nsc, p = read_u30(body, p)
    for _ in range(1, nsc):
        p += 1; _, p = read_u30(body, p)

    # Namespace set pool
    nssc, p = read_u30(body, p)
    for _ in range(1, nssc):
        cnt, p = read_u30(body, p)
        for _ in range(cnt): _, p = read_u30(body, p)

    # Multiname pool
    mnc, p = read_u30(body, p)
    mn = {}
    for i in range(1, mnc):
        k = body[p]; p += 1
        if k in (0x07, 0x0D):
            _, p = read_u30(body, p)
            ni, p = read_u30(body, p)
            if ni < len(sp): mn[i] = sp[ni]
        elif k in (0x0F, 0x10):
            _, p = read_u30(body, p)
        elif k in (0x11, 0x12):
            pass
        elif k in (0x09, 0x0E):
            ni, p = read_u30(body, p)
            _, p = read_u30(body, p)
            if ni < len(sp): mn[i] = sp[ni]
        elif k in (0x1B, 0x1C):
            _, p = read_u30(body, p)
        elif k == 0x1D:
            _, p = read_u30(body, p)
            pc, p = read_u30(body, p)
            for _ in range(pc): _, p = read_u30(body, p)

    # Find var_333 multiname
    var333_mn = None
    for idx, nm in mn.items():
        if nm == 'var_333':
            var333_mn = idx
    print(f"  var_333 multiname = {var333_mn}")

    # Method signatures
    mc, p = read_u30(body, p)
    for _ in range(mc):
        pc, p = read_u30(body, p)
        _, p = read_u30(body, p)
        for _ in range(pc): _, p = read_u30(body, p)
        _, p = read_u30(body, p)
        fl = body[p]; p += 1
        if fl & 0x08:
            oc, p = read_u30(body, p)
            for _ in range(oc): _, p = read_u30(body, p); p += 1
        if fl & 0x80:
            for _ in range(pc): _, p = read_u30(body, p)

    # Metadata
    mdc, p = read_u30(body, p)
    for _ in range(mdc):
        _, p = read_u30(body, p)
        ic2, p = read_u30(body, p)
        for _ in range(ic2): _, p = read_u30(body, p); _, p = read_u30(body, p)

    # Instance info — find DevSettings and Level classes
    cc, p = read_u30(body, p)
    dsi = None; lvl_i = None
    m1003 = None
    for i in range(cc):
        ni, p = read_u30(body, p)
        cn = mn.get(ni, '?')
        _, p = read_u30(body, p)
        fb = body[p]; p += 1
        if fb & 0x08: _, p = read_u30(body, p)
        ifc, p = read_u30(body, p)
        for _ in range(ifc): _, p = read_u30(body, p)
        _, p = read_u30(body, p)

        tc2, p = read_u30(body, p)
        for j in range(tc2):
            tn, tk, tm, p = read_trait_info(body, p, mn)
            if cn == 'Level' and tn == 'method_1003' and tk in (1, 2, 3):
                m1003 = tm
                print(f"  Level.method_1003 → method#{tm}")
        if cn == 'DevSettings': dsi = i
        if cn == 'Level': lvl_i = i

    if dsi is None:
        print("  DevSettings not found!"); return None
    if m1003 is None:
        print("  Level.method_1003 not found!"); return None

    # Class info — find DevSettings.flags trait
    fvp = None
    for i in range(cc):
        _, p = read_u30(body, p)
        tc2, p = read_u30(body, p)
        for j in range(tc2):
            tni, p2 = read_u30(body, p)
            tn = mn.get(tni, '?')
            tk = body[p2]; p2 += 1
            ki = tk & 0x0F; at = tk >> 4
            if ki in (0, 6):
                _, p2 = read_u30(body, p2)
                _, p2 = read_u30(body, p2)
                vip = p2
                vi, p2 = read_u30(body, p2)
                if vi: p2 += 1
                if i == dsi and tn == 'flags':
                    fvp = vip
                    print(f"  flags vindex={vi} at {vip}")
            elif ki in (1, 2, 3):
                _, p2 = read_u30(body, p2)
                _, p2 = read_u30(body, p2)
            elif ki == 4:
                _, p2 = read_u30(body, p2)
                _, p2 = read_u30(body, p2)
            elif ki == 5:
                _, p2 = read_u30(body, p2)
                _, p2 = read_u30(body, p2)
            if at & 0x04:
                mdc2, p2 = read_u30(body, p2)
                for _ in range(mdc2): _, p2 = read_u30(body, p2)
            p = p2

    # Script info
    scc, p = read_u30(body, p)
    for _ in range(scc):
        _, p = read_u30(body, p)
        tc2, p = read_u30(body, p)
        for _ in range(tc2): p = skip_trait(body, p)

    # Method bodies — find method_1003
    mbc, p = read_u30(body, p)
    cs1003 = None; cl1003 = None
    for _ in range(mbc):
        mbm, p = read_u30(body, p)
        for _ in range(4): _, p = read_u30(body, p)
        clen, p = read_u30(body, p)
        cs = p; p += clen
        exc, p = read_u30(body, p)
        for _ in range(exc):
            for _ in range(5): _, p = read_u30(body, p)
        tc2, p = read_u30(body, p)
        for _ in range(tc2): p = skip_trait(body, p)
        if mbm == m1003:
            cs1003 = cs; cl1003 = clen
            print(f"  method_1003 code at {cs}, len {clen}")

    if cs1003 is None:
        print("  method_1003 body not found!"); return None

    # === PATCH 2: Remove var_333 check in method_1003 ===
    code = bytes(body[cs1003:cs1003 + cl1003])
    instrs = disassemble(code)
    print(f"  Disassembled {len(instrs)} instructions")

    # Find: getproperty var_333 followed by iffalse
    target_iffalse_offset = None
    for i, (off, op, ops) in enumerate(instrs):
        if op == 0x66 and ops and ops[0][1] == var333_mn:
            print(f"  getproperty var_333 at instr#{i}, offset {off}")
            # Find next iffalse
            for j in range(i + 1, min(i + 5, len(instrs))):
                if instrs[j][1] == 0x12:  # iffalse
                    target_iffalse_offset = instrs[j][0]
                    branch_target = instrs[j][2][0][1]  # s24 offset
                    print(f"  iffalse at instr#{j}, offset {target_iffalse_offset}, target +{branch_target}")

                    # Show context
                    print(f"  Context:")
                    for x in range(max(0, i-2), min(len(instrs), j+4)):
                        o2, op2, ops2 = instrs[x]
                        nm = OPCODE_NAMES.get(op2, f'op_{op2:02X}')
                        if x == j:
                            marker = " <<<< PATCH: pop + 3×nop"
                        else:
                            marker = ""
                        ostr = ""
                        for ot, ov in ops2:
                            if ot == 'u30':
                                mname = mn.get(ov, '')
                                ostr += f" {ov}" + (f"({mname})" if mname else "")
                            elif ot == 's24': ostr += f" {ov:+d}"
                            else: ostr += f" {ov}"
                        print(f"    [{o2:4d}] {nm}{ostr}{marker}")
                    break
            break

    if target_iffalse_offset is None:
        print("  ERROR: iffalse after var_333 not found!"); return None

    # Replace iffalse (0x12 + s24 = 4 bytes) with pop + 3×nop
    abs_if = cs1003 + target_iffalse_offset
    assert body[abs_if] == 0x12, f"Expected 0x12 (iffalse) at {abs_if}, got 0x{body[abs_if]:02X}"
    body[abs_if] = 0x29    # pop (removes boolean, same stack effect as iffalse)
    body[abs_if+1] = 0x02  # nop
    body[abs_if+2] = 0x02  # nop
    body[abs_if+3] = 0x02  # nop
    print(f"  ✓ PATCH 2: iffalse → pop+3×nop at offset {abs_if}")
    print(f"    Cues now spawn for ALL levels, not just Home")

    # === PATCH 1: Set DevSettings.flags = 32 ===
    sd = 0
    if fvp is None:
        print("  flags trait not found!"); return None

    # AVM2 uint pool: count includes implicit entry[0]=0
    # count=0 means 1 implicit entry. To add entry[1], need count=2.
    oub = write_u30(uc); nub = write_u30(2)
    assert len(oub) == len(nub), "uint count encoding size changed!"
    body[ucp:ucp + len(oub)] = nub
    ip = ucp + len(nub)
    vb = write_u30(TARGET_FLAGS)
    body[ip:ip] = vb
    sd += len(vb)
    print(f"  ✓ PATCH 1a: uint_count={uc}→2, uint[1]={TARGET_FLAGS}")

    fvp += len(vb)  # adjust for bytes inserted before
    body[fvp] = 0x01  # vindex=1 (our new entry at index 1)
    body[fvp + 1:fvp + 1] = bytes([0x06])  # vkind=0x06 (uint)
    sd += 1
    print(f"  ✓ PATCH 1b: flags vindex=1, vkind=0x06 (uint)")

    print(f"\n  Summary:")
    print(f"    DevSettings.flags = {TARGET_FLAGS} (SPAWN_MONSTERS)")
    print(f"    Level.method_1003: var_333 check removed → cues spawn for all levels")
    print(f"    No STANDALONE_CLIENT → no crash, normal login flow preserved")
    print(f"    Size delta: +{sd}")

    return {'size_delta': sd}


if __name__ == '__main__':
    main()
