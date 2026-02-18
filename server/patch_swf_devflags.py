#!/usr/bin/env python3
"""
Patch DungeonBlitz.swf for client-side NPC spawning and projectile collision.

Patches (idempotent):
1) DevSettings.flags = 32 (DEVFLAG_SPAWN_MONSTERS)
2) Level.method_1003: remove var_333 gate (iffalse -> pop+nop+nop+nop)
3) class_130.<init>: replace standalone-client fallback for var_536 with
   Boolean(param6.var_275) + nop padding (fixed-length byte replacement)

This script is transactional: if any patch precondition is missing, no file write
occurs. It never edits files under extra-modules.
"""

from __future__ import annotations

import argparse
import dataclasses
import os
import shutil
import struct
import sys
import zlib
from typing import Dict, List, Optional, Sequence, Tuple

DEFAULT_SWF_PATH = "server/content/localhost/p/cbv/DungeonBlitz.swf"
TARGET_FLAGS = 32

STATUS_ALREADY = "already"
STATUS_NEEDS = "needs_patch"
STATUS_MISSING = "missing"


class PatchError(RuntimeError):
    pass


@dataclasses.dataclass
class PatchStatus:
    key: str
    status: str
    detail: str


@dataclasses.dataclass
class BytePatch:
    key: str
    start: int
    end: int
    data: bytes
    detail: str

    def delta(self) -> int:
        return len(self.data) - (self.end - self.start)


@dataclasses.dataclass
class SwfContext:
    path: str
    signature: str
    version: int
    body: bytearray
    doabc_tag_type: int
    doabc_len_field_pos: int
    doabc_len: int
    abc_start: int


@dataclasses.dataclass
class TraitInfo:
    name_idx: int
    kind_id: int
    method_idx: Optional[int]
    vindex: Optional[int]
    vindex_pos: Optional[int]
    vindex_len: int
    vkind: Optional[int]
    vkind_pos: Optional[int]


@dataclasses.dataclass
class InstanceInfo:
    class_name_idx: int
    iinit_method_idx: int
    traits: List[TraitInfo]


@dataclasses.dataclass
class ClassInfo:
    cinit_method_idx: int
    traits: List[TraitInfo]


@dataclasses.dataclass
class MethodBodyInfo:
    method_idx: int
    code_len_pos: int
    code_len: int
    code_start: int


@dataclasses.dataclass
class AbcParseResult:
    uint_count: int
    uint_count_pos: int
    uint_count_len: int
    uint_pool_start: int
    uint_values: List[int]
    uint_value_positions: List[int]
    multiname_names: List[str]
    instances: List[InstanceInfo]
    classes: List[ClassInfo]
    method_bodies: Dict[int, MethodBodyInfo]


@dataclasses.dataclass
class Instruction:
    offset: int
    opcode: int
    operands: List[Tuple[str, int]]
    size: int


# AVM2 opcode signatures
OPCODE_INFO: Dict[int, List[str]] = {}


def _init_opcode_info() -> None:
    no_args: List[int] = [
        0x01,
        0x02,
        0x03,
        0x07,
        0x09,
        0x1C,
        0x1D,
        0x1E,
        0x1F,
        0x20,
        0x21,
        0x23,
        0x26,
        0x27,
        0x28,
        0x29,
        0x2A,
        0x2B,
        0x30,
        0x35,
        0x36,
        0x37,
        0x38,
        0x39,
        0x3A,
        0x3B,
        0x3C,
        0x3D,
        0x3E,
        0x47,
        0x48,
        0x50,
        0x51,
        0x52,
        0x57,
        0x64,
        0x70,
        0x71,
        0x72,
        0x73,
        0x74,
        0x75,
        0x76,
        0x77,
        0x78,
        0x81,
        0x82,
        0x83,
        0x84,
        0x85,
        0x87,
        0x88,
        0x89,
        0x90,
        0x91,
        0x93,
        0x95,
        0x96,
        0x97,
        0xA0,
        0xA1,
        0xA2,
        0xA3,
        0xA4,
        0xA5,
        0xA6,
        0xA7,
        0xA8,
        0xA9,
        0xAA,
        0xAB,
        0xAC,
        0xAD,
        0xAE,
        0xAF,
        0xB0,
        0xB1,
        0xB3,
        0xB4,
        0xC0,
        0xC1,
        0xC4,
        0xC5,
        0xC6,
        0xC7,
        0xD0,
        0xD1,
        0xD2,
        0xD3,
        0xD4,
        0xD5,
        0xD6,
        0xD7,
    ]
    u30_args: List[int] = [
        0x04,
        0x05,
        0x06,
        0x08,
        0x25,
        0x2C,
        0x2D,
        0x2E,
        0x2F,
        0x31,
        0x40,
        0x41,
        0x42,
        0x49,
        0x53,
        0x55,
        0x56,
        0x58,
        0x59,
        0x5A,
        0x5D,
        0x5E,
        0x5F,
        0x60,
        0x61,
        0x62,
        0x63,
        0x65,
        0x66,
        0x68,
        0x6A,
        0x6C,
        0x6D,
        0x6E,
        0x6F,
        0x80,
        0x86,
        0x92,
        0x94,
        0xB2,
        0xC2,
        0xC3,
        0xF0,
        0xF1,
        0xF2,
    ]
    s24_args: List[int] = [
        0x0C,
        0x0D,
        0x0E,
        0x0F,
        0x10,
        0x11,
        0x12,
        0x13,
        0x14,
        0x15,
        0x16,
        0x17,
        0x18,
        0x19,
        0x1A,
    ]
    u30_u30_args: List[int] = [0x43, 0x44, 0x45, 0x46, 0x4A, 0x4C, 0x4E, 0x4F]

    for op in no_args:
        OPCODE_INFO[op] = []
    for op in u30_args:
        OPCODE_INFO[op] = ["u30"]
    for op in s24_args:
        OPCODE_INFO[op] = ["s24"]
    for op in u30_u30_args:
        OPCODE_INFO[op] = ["u30", "u30"]
    OPCODE_INFO[0x24] = ["s8"]
    OPCODE_INFO[0x32] = ["u30", "u30"]
    OPCODE_INFO[0xEF] = ["debug"]
    OPCODE_INFO[0x1B] = ["lookupswitch"]


_init_opcode_info()


def read_u30(data: Sequence[int], pos: int, ctx: str) -> Tuple[int, int]:
    value = 0
    shift = 0
    for _ in range(5):
        if pos >= len(data):
            raise PatchError(f"Out-of-bounds u30 read at {pos} ({ctx})")
        byte = data[pos]
        pos += 1
        value |= (byte & 0x7F) << shift
        if (byte & 0x80) == 0:
            return value, pos
        shift += 7
    return value, pos


def write_u30(value: int) -> bytes:
    if value < 0:
        raise PatchError(f"u30 cannot encode negative value {value}")
    out = bytearray()
    while True:
        b = value & 0x7F
        value >>= 7
        if value:
            b |= 0x80
        out.append(b)
        if not value:
            return bytes(out)


def read_s32(data: Sequence[int], pos: int, ctx: str) -> Tuple[int, int]:
    value = 0
    shift = 0
    last = 0
    for _ in range(5):
        if pos >= len(data):
            raise PatchError(f"Out-of-bounds s32 read at {pos} ({ctx})")
        b = data[pos]
        pos += 1
        last = b
        value |= (b & 0x7F) << shift
        shift += 7
        if (b & 0x80) == 0:
            break
    if shift < 32 and (last & 0x40):
        value |= -(1 << shift)
    return value, pos


def read_s24(data: Sequence[int], pos: int, ctx: str) -> Tuple[int, int]:
    if pos + 3 > len(data):
        raise PatchError(f"Out-of-bounds s24 read at {pos} ({ctx})")
    value = data[pos] | (data[pos + 1] << 8) | (data[pos + 2] << 16)
    if value & 0x800000:
        value -= 0x1000000
    return value, pos + 3


def read_cstring(data: Sequence[int], pos: int, end: int, ctx: str) -> Tuple[str, int]:
    start = pos
    while pos < end and data[pos] != 0:
        pos += 1
    if pos >= end:
        raise PatchError(f"Unterminated cstring ({ctx})")
    raw = bytes(data[start:pos])
    return raw.decode("utf-8", errors="replace"), pos + 1


def parse_swf(path: str) -> SwfContext:
    with open(path, "rb") as f:
        raw = f.read()
    if len(raw) < 8:
        raise PatchError("SWF too short")

    signature = raw[0:3].decode("ascii", errors="replace")
    version = raw[3]

    if signature == "CWS":
        try:
            body = bytearray(zlib.decompress(raw[8:]))
        except Exception as exc:
            raise PatchError(f"Failed to decompress CWS body: {exc}") from exc
    elif signature == "FWS":
        body = bytearray(raw[8:])
    else:
        raise PatchError(f"Unsupported SWF signature: {signature}")

    if not body:
        raise PatchError("SWF body is empty")

    # Skip RECT + frame rate + frame count
    nbits = body[0] >> 3
    pos = (5 + nbits * 4 + 7) // 8 + 4

    doabc_tag_type = -1
    doabc_len_field_pos = -1
    doabc_len = -1
    abc_start = -1

    while pos < len(body):
        if pos + 2 > len(body):
            raise PatchError(f"Tag header truncated at {pos}")
        tag_code_and_len = struct.unpack_from("<H", body, pos)[0]
        pos += 2
        tag_type = tag_code_and_len >> 6
        tag_len = tag_code_and_len & 0x3F
        tag_len_field_pos = pos
        if tag_len == 0x3F:
            if pos + 4 > len(body):
                raise PatchError(f"Long tag length truncated at {pos}")
            tag_len = struct.unpack_from("<I", body, pos)[0]
            pos += 4
        tag_data_start = pos
        tag_data_end = tag_data_start + tag_len
        if tag_data_end > len(body):
            raise PatchError(
                f"Tag {tag_type} at {tag_data_start} overruns body ({tag_data_end} > {len(body)})"
            )

        if tag_type in (82, 72):
            # Prefer DoABC2 (82). Use first ABC tag encountered.
            if abc_start == -1:
                if tag_type == 82:
                    if tag_data_start + 4 > tag_data_end:
                        raise PatchError("DoABC2 tag too short for flags")
                    name, after_name = read_cstring(
                        body,
                        tag_data_start + 4,
                        tag_data_end,
                        "DoABC2 name",
                    )
                    _ = name
                    abc_start = after_name
                else:
                    # SWF DoABC (72) has ABC payload directly.
                    abc_start = tag_data_start
                doabc_tag_type = tag_type
                doabc_len_field_pos = tag_len_field_pos
                doabc_len = tag_len

        pos = tag_data_end

    if abc_start == -1:
        raise PatchError("No DoABC/DoABC2 tag found")
    if doabc_len_field_pos == -1:
        raise PatchError("Internal error: DoABC length field position missing")

    return SwfContext(
        path=path,
        signature=signature,
        version=version,
        body=body,
        doabc_tag_type=doabc_tag_type,
        doabc_len_field_pos=doabc_len_field_pos,
        doabc_len=doabc_len,
        abc_start=abc_start,
    )


def parse_trait(data: bytearray, pos: int, ctx: str) -> Tuple[TraitInfo, int]:
    name_idx, pos = read_u30(data, pos, f"{ctx}.trait.name")
    if pos >= len(data):
        raise PatchError(f"Out-of-bounds trait kind at {pos} ({ctx})")
    kind = data[pos]
    pos += 1
    kind_id = kind & 0x0F
    attrs = kind >> 4

    method_idx: Optional[int] = None
    vindex: Optional[int] = None
    vindex_pos: Optional[int] = None
    vindex_len = 0
    vkind: Optional[int] = None
    vkind_pos: Optional[int] = None

    if kind_id in (0, 6):
        _, pos = read_u30(data, pos, f"{ctx}.trait.slot_id")
        _, pos = read_u30(data, pos, f"{ctx}.trait.type_name")
        vindex_pos = pos
        vindex, pos = read_u30(data, pos, f"{ctx}.trait.vindex")
        vindex_len = pos - vindex_pos
        if vindex:
            if pos >= len(data):
                raise PatchError(f"Out-of-bounds vkind read at {pos} ({ctx})")
            vkind_pos = pos
            vkind = data[pos]
            pos += 1
    elif kind_id in (1, 2, 3):
        _, pos = read_u30(data, pos, f"{ctx}.trait.disp_id")
        method_idx, pos = read_u30(data, pos, f"{ctx}.trait.method")
    elif kind_id == 4:
        _, pos = read_u30(data, pos, f"{ctx}.trait.slot_id")
        _, pos = read_u30(data, pos, f"{ctx}.trait.classi")
    elif kind_id == 5:
        _, pos = read_u30(data, pos, f"{ctx}.trait.slot_id")
        _, pos = read_u30(data, pos, f"{ctx}.trait.functioni")
    else:
        raise PatchError(f"Unsupported trait kind id {kind_id} ({ctx})")

    if attrs & 0x04:
        metadata_count, pos = read_u30(data, pos, f"{ctx}.trait.metadata_count")
        for i in range(metadata_count):
            _, pos = read_u30(data, pos, f"{ctx}.trait.metadata[{i}]")

    return (
        TraitInfo(
            name_idx=name_idx,
            kind_id=kind_id,
            method_idx=method_idx,
            vindex=vindex,
            vindex_pos=vindex_pos,
            vindex_len=vindex_len,
            vkind=vkind,
            vkind_pos=vkind_pos,
        ),
        pos,
    )


def parse_abc(ctx: SwfContext) -> AbcParseResult:
    data = ctx.body
    pos = ctx.abc_start

    if pos + 4 > len(data):
        raise PatchError("ABC header truncated (minor/major)")
    # minor_version + major_version
    pos += 4

    # int pool
    int_count, pos = read_u30(data, pos, "abc.int_count")
    for i in range(1, int_count):
        _, pos = read_s32(data, pos, f"abc.int[{i}]")

    # uint pool
    uint_count_pos = pos
    uint_count, pos = read_u30(data, pos, "abc.uint_count")
    uint_count_len = pos - uint_count_pos
    uint_pool_start = pos
    uint_values = [0]
    uint_value_positions = [0]
    for i in range(1, uint_count):
        entry_pos = pos
        value, pos = read_u30(data, pos, f"abc.uint[{i}]")
        uint_values.append(value)
        uint_value_positions.append(entry_pos)

    # double pool
    double_count, pos = read_u30(data, pos, "abc.double_count")
    if double_count > 0:
        jump = 8 * (double_count - 1)
        if pos + jump > len(data):
            raise PatchError("Double pool overruns ABC")
        pos += jump

    # string pool
    string_count, pos = read_u30(data, pos, "abc.string_count")
    strings = [""]
    for i in range(1, string_count):
        strlen, pos = read_u30(data, pos, f"abc.string[{i}].len")
        if pos + strlen > len(data):
            raise PatchError(f"String {i} overruns ABC")
        s = bytes(data[pos : pos + strlen]).decode("utf-8", errors="replace")
        strings.append(s)
        pos += strlen

    # namespace pool
    namespace_count, pos = read_u30(data, pos, "abc.namespace_count")
    for i in range(1, namespace_count):
        if pos >= len(data):
            raise PatchError(f"Namespace kind out-of-bounds for ns[{i}]")
        pos += 1
        _, pos = read_u30(data, pos, f"abc.namespace[{i}].name")

    # namespace set pool
    ns_set_count, pos = read_u30(data, pos, "abc.ns_set_count")
    for i in range(1, ns_set_count):
        cnt, pos = read_u30(data, pos, f"abc.ns_set[{i}].count")
        for j in range(cnt):
            _, pos = read_u30(data, pos, f"abc.ns_set[{i}][{j}]")

    # multiname pool
    multiname_count, pos = read_u30(data, pos, "abc.multiname_count")
    multiname_names = [""]
    for i in range(1, multiname_count):
        if pos >= len(data):
            raise PatchError(f"Multiname kind out-of-bounds for mn[{i}]")
        kind = data[pos]
        pos += 1
        name = ""
        if kind in (0x07, 0x0D):
            _, pos = read_u30(data, pos, f"abc.mn[{i}].ns")
            name_idx, pos = read_u30(data, pos, f"abc.mn[{i}].name")
            if name_idx < len(strings):
                name = strings[name_idx]
        elif kind in (0x0F, 0x10):
            name_idx, pos = read_u30(data, pos, f"abc.mn[{i}].name")
            if name_idx < len(strings):
                name = strings[name_idx]
        elif kind in (0x11, 0x12):
            pass
        elif kind in (0x09, 0x0E):
            name_idx, pos = read_u30(data, pos, f"abc.mn[{i}].name")
            _, pos = read_u30(data, pos, f"abc.mn[{i}].nsset")
            if name_idx < len(strings):
                name = strings[name_idx]
        elif kind in (0x1B, 0x1C):
            name_idx, pos = read_u30(data, pos, f"abc.mn[{i}].name")
            if name_idx < len(strings):
                name = strings[name_idx]
        elif kind == 0x1D:
            _, pos = read_u30(data, pos, f"abc.mn[{i}].qname")
            param_count, pos = read_u30(data, pos, f"abc.mn[{i}].param_count")
            for j in range(param_count):
                _, pos = read_u30(data, pos, f"abc.mn[{i}].param[{j}]")
        else:
            raise PatchError(f"Unsupported multiname kind 0x{kind:02X} at index {i}")
        multiname_names.append(name)

    # method_info
    method_count, pos = read_u30(data, pos, "abc.method_count")
    for i in range(method_count):
        param_count, pos = read_u30(data, pos, f"abc.method[{i}].param_count")
        _, pos = read_u30(data, pos, f"abc.method[{i}].return_type")
        for j in range(param_count):
            _, pos = read_u30(data, pos, f"abc.method[{i}].param_type[{j}]")
        _, pos = read_u30(data, pos, f"abc.method[{i}].name")
        if pos >= len(data):
            raise PatchError(f"Method flags out-of-bounds for method[{i}]")
        flags = data[pos]
        pos += 1
        if flags & 0x08:
            option_count, pos = read_u30(data, pos, f"abc.method[{i}].option_count")
            for j in range(option_count):
                _, pos = read_u30(data, pos, f"abc.method[{i}].option[{j}].val")
                if pos >= len(data):
                    raise PatchError(f"Method option kind out-of-bounds for method[{i}] opt[{j}]")
                pos += 1
        if flags & 0x80:
            for j in range(param_count):
                _, pos = read_u30(data, pos, f"abc.method[{i}].param_name[{j}]")

    # metadata
    metadata_count, pos = read_u30(data, pos, "abc.metadata_count")
    for i in range(metadata_count):
        _, pos = read_u30(data, pos, f"abc.metadata[{i}].name")
        item_count, pos = read_u30(data, pos, f"abc.metadata[{i}].item_count")
        for j in range(item_count):
            _, pos = read_u30(data, pos, f"abc.metadata[{i}].key[{j}]")
            _, pos = read_u30(data, pos, f"abc.metadata[{i}].val[{j}]")

    # instance_info
    class_count, pos = read_u30(data, pos, "abc.class_count")
    instances: List[InstanceInfo] = []
    for i in range(class_count):
        class_name_idx, pos = read_u30(data, pos, f"abc.instance[{i}].name")
        _, pos = read_u30(data, pos, f"abc.instance[{i}].super_name")
        if pos >= len(data):
            raise PatchError(f"Instance flags out-of-bounds for instance[{i}]")
        flags = data[pos]
        pos += 1
        if flags & 0x08:
            _, pos = read_u30(data, pos, f"abc.instance[{i}].protected_ns")
        interface_count, pos = read_u30(data, pos, f"abc.instance[{i}].interface_count")
        for j in range(interface_count):
            _, pos = read_u30(data, pos, f"abc.instance[{i}].interface[{j}]")
        iinit_method_idx, pos = read_u30(data, pos, f"abc.instance[{i}].iinit")
        trait_count, pos = read_u30(data, pos, f"abc.instance[{i}].trait_count")
        traits: List[TraitInfo] = []
        for j in range(trait_count):
            trait, pos = parse_trait(data, pos, f"abc.instance[{i}].trait[{j}]")
            traits.append(trait)
        instances.append(
            InstanceInfo(
                class_name_idx=class_name_idx,
                iinit_method_idx=iinit_method_idx,
                traits=traits,
            )
        )

    # class_info
    classes: List[ClassInfo] = []
    for i in range(class_count):
        cinit_method_idx, pos = read_u30(data, pos, f"abc.class[{i}].cinit")
        trait_count, pos = read_u30(data, pos, f"abc.class[{i}].trait_count")
        traits: List[TraitInfo] = []
        for j in range(trait_count):
            trait, pos = parse_trait(data, pos, f"abc.class[{i}].trait[{j}]")
            traits.append(trait)
        classes.append(ClassInfo(cinit_method_idx=cinit_method_idx, traits=traits))

    # script_info
    script_count, pos = read_u30(data, pos, "abc.script_count")
    for i in range(script_count):
        _, pos = read_u30(data, pos, f"abc.script[{i}].init")
        trait_count, pos = read_u30(data, pos, f"abc.script[{i}].trait_count")
        for j in range(trait_count):
            _, pos = parse_trait(data, pos, f"abc.script[{i}].trait[{j}]")

    # method_body_info
    method_body_count, pos = read_u30(data, pos, "abc.method_body_count")
    method_bodies: Dict[int, MethodBodyInfo] = {}
    for i in range(method_body_count):
        method_idx, pos = read_u30(data, pos, f"abc.mbody[{i}].method")
        _, pos = read_u30(data, pos, f"abc.mbody[{i}].max_stack")
        _, pos = read_u30(data, pos, f"abc.mbody[{i}].local_count")
        _, pos = read_u30(data, pos, f"abc.mbody[{i}].init_scope_depth")
        _, pos = read_u30(data, pos, f"abc.mbody[{i}].max_scope_depth")
        code_len_pos = pos
        code_len, pos = read_u30(data, pos, f"abc.mbody[{i}].code_length")
        code_start = pos
        code_end = code_start + code_len
        if code_end > len(data):
            raise PatchError(f"Method body {i} code overruns ABC")
        pos = code_end

        exception_count, pos = read_u30(data, pos, f"abc.mbody[{i}].exception_count")
        for j in range(exception_count):
            _, pos = read_u30(data, pos, f"abc.mbody[{i}].exception[{j}].from")
            _, pos = read_u30(data, pos, f"abc.mbody[{i}].exception[{j}].to")
            _, pos = read_u30(data, pos, f"abc.mbody[{i}].exception[{j}].target")
            _, pos = read_u30(data, pos, f"abc.mbody[{i}].exception[{j}].exc_type")
            _, pos = read_u30(data, pos, f"abc.mbody[{i}].exception[{j}].var_name")

        trait_count, pos = read_u30(data, pos, f"abc.mbody[{i}].trait_count")
        for j in range(trait_count):
            _, pos = parse_trait(data, pos, f"abc.mbody[{i}].trait[{j}]")

        method_bodies[method_idx] = MethodBodyInfo(
            method_idx=method_idx,
            code_len_pos=code_len_pos,
            code_len=code_len,
            code_start=code_start,
        )

    return AbcParseResult(
        uint_count=uint_count,
        uint_count_pos=uint_count_pos,
        uint_count_len=uint_count_len,
        uint_pool_start=uint_pool_start,
        uint_values=uint_values,
        uint_value_positions=uint_value_positions,
        multiname_names=multiname_names,
        instances=instances,
        classes=classes,
        method_bodies=method_bodies,
    )


def disassemble(code: bytes, ctx: str) -> List[Instruction]:
    out: List[Instruction] = []
    pos = 0
    while pos < len(code):
        start = pos
        op = code[pos]
        pos += 1
        operands: List[Tuple[str, int]] = []
        arg_spec = OPCODE_INFO.get(op)
        if arg_spec is None:
            raise PatchError(f"Unknown opcode 0x{op:02X} at byte {start} ({ctx})")
        for arg_kind in arg_spec:
            if arg_kind == "u30":
                v, pos = read_u30(code, pos, f"{ctx}.op@{start}.u30")
                operands.append(("u30", v))
            elif arg_kind == "s24":
                v, pos = read_s24(code, pos, f"{ctx}.op@{start}.s24")
                operands.append(("s24", v))
            elif arg_kind == "s8":
                if pos >= len(code):
                    raise PatchError(f"Out-of-bounds s8 at {pos} ({ctx})")
                v = code[pos]
                if v > 127:
                    v -= 256
                pos += 1
                operands.append(("s8", v))
            elif arg_kind == "debug":
                if pos >= len(code):
                    raise PatchError(f"Out-of-bounds debug header at {pos} ({ctx})")
                dt = code[pos]
                pos += 1
                idx, pos = read_u30(code, pos, f"{ctx}.op@{start}.debug.idx")
                if pos >= len(code):
                    raise PatchError(f"Out-of-bounds debug reg at {pos} ({ctx})")
                reg = code[pos]
                pos += 1
                extra, pos = read_u30(code, pos, f"{ctx}.op@{start}.debug.extra")
                operands.extend([("u8", dt), ("u30", idx), ("u8", reg), ("u30", extra)])
            elif arg_kind == "lookupswitch":
                default_off, pos = read_s24(code, pos, f"{ctx}.op@{start}.lookupswitch.default")
                case_count, pos = read_u30(code, pos, f"{ctx}.op@{start}.lookupswitch.case_count")
                operands.append(("s24", default_off))
                operands.append(("u30", case_count))
                for i in range(case_count + 1):
                    case_off, pos = read_s24(code, pos, f"{ctx}.op@{start}.lookupswitch.case[{i}]")
                    operands.append(("s24", case_off))
            else:
                raise PatchError(f"Unsupported operand kind: {arg_kind}")
        out.append(Instruction(offset=start, opcode=op, operands=operands, size=pos - start))
    return out


def u30_operand_name(inst: Instruction, mn_names: List[str]) -> str:
    for t, v in inst.operands:
        if t == "u30":
            if 0 <= v < len(mn_names):
                return mn_names[v]
            return ""
    return ""


def getlocal_index(inst: Instruction) -> Optional[int]:
    if inst.opcode == 0x62:  # getlocal
        for t, v in inst.operands:
            if t == "u30":
                return v
        return None
    if 0xD0 <= inst.opcode <= 0xD7:  # getlocal_0..7
        return inst.opcode - 0xD0
    return None


def class_index_by_name(abc: AbcParseResult, class_name: str) -> Optional[int]:
    for i, inst in enumerate(abc.instances):
        idx = inst.class_name_idx
        if 0 <= idx < len(abc.multiname_names) and abc.multiname_names[idx] == class_name:
            return i
    return None


def method_idx_for_trait(
    traits: Sequence[TraitInfo],
    abc: AbcParseResult,
    trait_name: str,
) -> Optional[int]:
    for tr in traits:
        if tr.method_idx is None:
            continue
        if 0 <= tr.name_idx < len(abc.multiname_names) and abc.multiname_names[tr.name_idx] == trait_name:
            return tr.method_idx
    return None


def analyze_patch_devsettings_flags(abc: AbcParseResult) -> Tuple[PatchStatus, List[BytePatch]]:
    ci = class_index_by_name(abc, "DevSettings")
    if ci is None:
        return PatchStatus("devsettings_flags", STATUS_MISSING, "DevSettings class not found"), []
    if ci >= len(abc.classes):
        return PatchStatus("devsettings_flags", STATUS_MISSING, "DevSettings class_info missing"), []

    flags_trait: Optional[TraitInfo] = None
    for tr in abc.classes[ci].traits:
        if tr.kind_id not in (0, 6):
            continue
        if 0 <= tr.name_idx < len(abc.multiname_names) and abc.multiname_names[tr.name_idx] == "flags":
            flags_trait = tr
            break

    if flags_trait is None:
        return PatchStatus("devsettings_flags", STATUS_MISSING, "DevSettings.flags trait not found"), []
    if flags_trait.vindex_pos is None:
        return PatchStatus("devsettings_flags", STATUS_MISSING, "DevSettings.flags vindex position missing"), []

    uint_ok = (
        abc.uint_count >= 2
        and len(abc.uint_values) > 1
        and abc.uint_values[1] == TARGET_FLAGS
    )
    flags_ok = flags_trait.vindex == 1 and flags_trait.vkind == 0x06

    if uint_ok and flags_ok:
        return PatchStatus(
            "devsettings_flags",
            STATUS_ALREADY,
            "uint[1]=32 and DevSettings.flags vindex=1/vkind=0x06",
        ), []

    patches: List[BytePatch] = []

    # Patch vindex/vkind first (higher offset than uint pool in this SWF).
    current_vindex = flags_trait.vindex if flags_trait.vindex is not None else 0
    vindex_pos = flags_trait.vindex_pos
    vindex_len = flags_trait.vindex_len
    new_vindex_bytes = write_u30(1)
    if vindex_len != len(new_vindex_bytes):
        return (
            PatchStatus(
                "devsettings_flags",
                STATUS_MISSING,
                f"Unsupported vindex size change ({vindex_len} -> {len(new_vindex_bytes)})",
            ),
            [],
        )

    if current_vindex != 1:
        patches.append(
            BytePatch(
                key="devsettings_flags",
                start=vindex_pos,
                end=vindex_pos + vindex_len,
                data=new_vindex_bytes,
                detail="Set DevSettings.flags vindex=1",
            )
        )

    if current_vindex == 0:
        insert_pos = vindex_pos + vindex_len
        patches.append(
            BytePatch(
                key="devsettings_flags",
                start=insert_pos,
                end=insert_pos,
                data=b"\x06",
                detail="Insert DevSettings.flags vkind=0x06 (uint)",
            )
        )
    elif flags_trait.vkind is not None and flags_trait.vkind != 0x06 and flags_trait.vkind_pos is not None:
        patches.append(
            BytePatch(
                key="devsettings_flags",
                start=flags_trait.vkind_pos,
                end=flags_trait.vkind_pos + 1,
                data=b"\x06",
                detail="Set DevSettings.flags vkind=0x06 (uint)",
            )
        )

    # Patch uint pool.
    if abc.uint_count < 2:
        old_count_bytes = write_u30(abc.uint_count)
        new_count_bytes = write_u30(2)
        if len(old_count_bytes) != abc.uint_count_len or len(new_count_bytes) != abc.uint_count_len:
            return (
                PatchStatus(
                    "devsettings_flags",
                    STATUS_MISSING,
                    "Unsupported uint_count encoding width change",
                ),
                [],
            )

        patches.append(
            BytePatch(
                key="devsettings_flags",
                start=abc.uint_count_pos,
                end=abc.uint_count_pos + abc.uint_count_len,
                data=new_count_bytes,
                detail="Set uint_count=2",
            )
        )
        patches.append(
            BytePatch(
                key="devsettings_flags",
                start=abc.uint_pool_start,
                end=abc.uint_pool_start,
                data=write_u30(TARGET_FLAGS),
                detail="Insert uint[1]=32",
            )
        )
    else:
        value_pos = abc.uint_value_positions[1]
        current = abc.uint_values[1]
        current_bytes = write_u30(current)
        desired_bytes = write_u30(TARGET_FLAGS)
        if len(current_bytes) != len(desired_bytes):
            return (
                PatchStatus(
                    "devsettings_flags",
                    STATUS_MISSING,
                    f"Unsupported uint[1] varint width change ({len(current_bytes)} -> {len(desired_bytes)})",
                ),
                [],
            )
        if current != TARGET_FLAGS:
            patches.append(
                BytePatch(
                    key="devsettings_flags",
                    start=value_pos,
                    end=value_pos + len(current_bytes),
                    data=desired_bytes,
                    detail=f"Set uint[1]={TARGET_FLAGS}",
                )
            )

    if not patches:
        return PatchStatus(
            "devsettings_flags",
            STATUS_ALREADY,
            "No changes needed",
        ), []

    return PatchStatus("devsettings_flags", STATUS_NEEDS, "DevSettings.flags patch required"), patches


def analyze_patch_level_method_1003(abc: AbcParseResult, body: bytearray) -> Tuple[PatchStatus, List[BytePatch]]:
    ci = class_index_by_name(abc, "Level")
    if ci is None:
        return PatchStatus("level_method_1003", STATUS_MISSING, "Level class not found"), []

    method_idx = method_idx_for_trait(abc.instances[ci].traits, abc, "method_1003")
    if method_idx is None:
        return PatchStatus("level_method_1003", STATUS_MISSING, "Level.method_1003 not found"), []

    mbody = abc.method_bodies.get(method_idx)
    if mbody is None:
        return PatchStatus("level_method_1003", STATUS_MISSING, "method_1003 body not found"), []

    code = bytes(body[mbody.code_start : mbody.code_start + mbody.code_len])
    instrs = disassemble(code, "Level.method_1003")

    candidate_offsets: List[int] = []
    for i, inst in enumerate(instrs):
        if inst.opcode != 0x66:
            continue
        if u30_operand_name(inst, abc.multiname_names) != "var_333":
            continue
        for j in range(i + 1, min(i + 8, len(instrs))):
            off = instrs[j].offset
            if off + 4 > len(code):
                continue
            chunk = code[off : off + 4]
            if chunk == b"\x29\x02\x02\x02":
                return (
                    PatchStatus(
                        "level_method_1003",
                        STATUS_ALREADY,
                        f"var_333 gate already replaced at code offset {off}",
                    ),
                    [],
                )
            if instrs[j].opcode == 0x12:
                candidate_offsets.append(off)
                break
        if candidate_offsets:
            break

    if not candidate_offsets:
        return (
            PatchStatus(
                "level_method_1003",
                STATUS_MISSING,
                "Could not find var_333 iffalse branch in method_1003",
            ),
            [],
        )

    off = candidate_offsets[0]
    patch = BytePatch(
        key="level_method_1003",
        start=mbody.code_start + off,
        end=mbody.code_start + off + 4,
        data=b"\x29\x02\x02\x02",
        detail=f"Replace iffalse with pop+nop+nop+nop at code offset {off}",
    )
    return PatchStatus("level_method_1003", STATUS_NEEDS, "method_1003 var_333 gate patch required"), [patch]


def infer_powertype_local(instrs: List[Instruction], mn_names: List[str]) -> Optional[int]:
    for i, inst in enumerate(instrs):
        if inst.opcode != 0x66:
            continue
        if u30_operand_name(inst, mn_names) != "var_275":
            continue
        if i == 0:
            continue
        idx = getlocal_index(instrs[i - 1])
        if idx is not None:
            return idx
    return None


def encode_getlocal(idx: int) -> bytes:
    if idx < 0:
        raise PatchError(f"Invalid local register index {idx}")
    return bytes([0x62]) + write_u30(idx)


def analyze_patch_class130_projectile(
    abc: AbcParseResult,
    body: bytearray,
) -> Tuple[PatchStatus, List[BytePatch]]:
    ci = class_index_by_name(abc, "class_130")
    if ci is None:
        return PatchStatus("class130_projectile", STATUS_MISSING, "class_130 not found"), []

    method_idx = abc.instances[ci].iinit_method_idx
    mbody = abc.method_bodies.get(method_idx)
    if mbody is None:
        return PatchStatus("class130_projectile", STATUS_MISSING, "class_130.<init> body not found"), []

    code = bytes(body[mbody.code_start : mbody.code_start + mbody.code_len])
    instrs = disassemble(code, "class_130.<init>")

    powertype_local = infer_powertype_local(instrs, abc.multiname_names)
    if powertype_local is None:
        return PatchStatus("class130_projectile", STATUS_MISSING, "Could not infer powerType local register"), []

    var275_idx = None
    var536_idx = None
    for i, name in enumerate(abc.multiname_names):
        if name == "var_275" and var275_idx is None:
            var275_idx = i
        if name == "var_536" and var536_idx is None:
            var536_idx = i
    if var275_idx is None:
        return PatchStatus("class130_projectile", STATUS_MISSING, "var_275 multiname not found"), []
    if var536_idx is None:
        return PatchStatus("class130_projectile", STATUS_MISSING, "var_536 multiname not found"), []

    new_core = b"\x29" + encode_getlocal(powertype_local) + b"\x66" + write_u30(var275_idx) + b"\x76"

    # Locate initproperty var_536
    target_i = -1
    for i, inst in enumerate(instrs):
        if inst.opcode != 0x68:
            continue
        if not inst.operands:
            continue
        if inst.operands[0][0] != "u30":
            continue
        if inst.operands[0][1] == var536_idx:
            target_i = i
            break
    if target_i == -1:
        return PatchStatus("class130_projectile", STATUS_MISSING, "initproperty var_536 not found"), []

    # Old sequence we replace:
    # pop; getlex DevSettings; getproperty flags; getlex DevSettings;
    # getproperty DEVFLAG_STANDALONE_CLIENT; bitand; convert_b
    old_match = False
    old_start = None
    old_end = instrs[target_i].offset
    if target_i >= 7:
        seq = instrs[target_i - 7 : target_i]
        names = [u30_operand_name(x, abc.multiname_names) for x in seq]
        if (
            seq[0].opcode == 0x29
            and seq[1].opcode == 0x60
            and names[1] == "DevSettings"
            and seq[2].opcode == 0x66
            and names[2] == "flags"
            and seq[3].opcode == 0x60
            and names[3] == "DevSettings"
            and seq[4].opcode == 0x66
            and names[4] == "DEVFLAG_STANDALONE_CLIENT"
            and seq[5].opcode == 0xA8
            and seq[6].opcode == 0x76
        ):
            old_match = True
            old_start = seq[0].offset

    if old_match and old_start is not None:
        region_len = old_end - old_start
        if region_len < len(new_core):
            return (
                PatchStatus(
                    "class130_projectile",
                    STATUS_MISSING,
                    f"Replacement core larger than target region ({len(new_core)} > {region_len})",
                ),
                [],
            )
        replacement = new_core + (b"\x02" * (region_len - len(new_core)))
        patch = BytePatch(
            key="class130_projectile",
            start=mbody.code_start + old_start,
            end=mbody.code_start + old_end,
            data=replacement,
            detail=(
                "Replace class_130 var_536 fallback with Boolean(param6.var_275) "
                f"at code offsets {old_start}-{old_end}"
            ),
        )
        return PatchStatus("class130_projectile", STATUS_NEEDS, "class_130 projectile collision patch required"), [patch]

    # Already patched check: look for new_core followed only by nops before initproperty.
    search_start = max(0, old_end - 32)
    found_already = False
    for start in range(search_start, old_end - len(new_core) + 1):
        if code[start : start + len(new_core)] != new_core:
            continue
        tail = code[start + len(new_core) : old_end]
        if all(b == 0x02 for b in tail):
            found_already = True
            break

    if found_already:
        return (
            PatchStatus(
                "class130_projectile",
                STATUS_ALREADY,
                "class_130 var_536 fallback already patched",
            ),
            [],
        )

    return (
        PatchStatus(
            "class130_projectile",
            STATUS_MISSING,
            "Expected class_130 var_536 fallback sequence not found",
        ),
        [],
    )





def format_status(status: PatchStatus) -> str:
    return f"[{status.key}] {status.status}: {status.detail}"

def apply_patches(body: bytearray, patches: Sequence[BytePatch]) -> int:
    # Apply from high to low offsets so absolute offsets stay valid.
    ordered = sorted(patches, key=lambda p: p.start, reverse=True)
    delta = 0
    for p in ordered:
        if p.start < 0 or p.end < p.start or p.end > len(body):
            raise PatchError(
                f"Invalid patch range for {p.key}: {p.start}:{p.end} (body len={len(body)})"
            )
        body[p.start : p.end] = p.data
        delta += p.delta()
    return delta


def write_swf(ctx: SwfContext, out_body: bytearray, abc_delta: int) -> None:
    # Update DoABC tag length if body size changed.
    if abc_delta:
        new_tag_len = ctx.doabc_len + abc_delta
        if new_tag_len < 0:
            raise PatchError(f"Negative DoABC length after delta: {new_tag_len}")
        struct.pack_into("<I", out_body, ctx.doabc_len_field_pos, new_tag_len)

    file_len_uncompressed = 8 + len(out_body)
    header = bytearray()
    header.extend(ctx.signature.encode("ascii"))
    header.append(ctx.version)
    header.extend(struct.pack("<I", file_len_uncompressed))

    if ctx.signature == "CWS":
        compressed = zlib.compress(bytes(out_body))
        payload = bytes(header) + compressed
    elif ctx.signature == "FWS":
        payload = bytes(header) + bytes(out_body)
    else:
        raise PatchError(f"Unsupported signature on write: {ctx.signature}")

    with open(ctx.path, "wb") as f:
        f.write(payload)


def ensure_backup(path: str) -> str:
    backup = path + ".bak"
    if not os.path.exists(backup):
        shutil.copy2(path, backup)
    return backup


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Patch DungeonBlitz.swf bytecode")
    parser.add_argument("--verify", action="store_true", help="Read-only patch status report")
    parser.add_argument("--dry-run", action="store_true", help="Resolve and report planned changes without writing")
    parser.add_argument("--swf-path", default=DEFAULT_SWF_PATH, help="Target SWF path")
    args = parser.parse_args(argv)

    if args.verify and args.dry_run:
        print("Cannot use --verify and --dry-run together", file=sys.stderr)
        return 2

    try:
        ctx = parse_swf(args.swf_path)
        abc = parse_abc(ctx)

        statuses: List[PatchStatus] = []
        all_patches: List[BytePatch] = []

        st1, p1 = analyze_patch_devsettings_flags(abc)
        statuses.append(st1)
        all_patches.extend(p1)

        st2, p2 = analyze_patch_level_method_1003(abc, ctx.body)
        statuses.append(st2)
        all_patches.extend(p2)

        st3, p3 = analyze_patch_class130_projectile(abc, ctx.body)
        statuses.append(st3)
        all_patches.extend(p3)


        print(f"SWF: {args.swf_path}")
        print(f"ABC tag type: {ctx.doabc_tag_type}, tag length: {ctx.doabc_len}")
        for st in statuses:
            print(format_status(st))

        has_missing = any(st.status == STATUS_MISSING for st in statuses)
        if args.verify:
            return 1 if has_missing else 0

        if has_missing:
            print("Aborting: one or more required patch preconditions are missing.", file=sys.stderr)
            return 1

        needs = [st for st in statuses if st.status == STATUS_NEEDS]
        if not needs:
            print("No changes needed.")
            return 0

        total_delta = sum(p.delta() for p in all_patches)
        print("Planned byte patches:")
        for p in sorted(all_patches, key=lambda x: x.start):
            print(f"  - [{p.key}] {p.detail} @ {p.start}:{p.end} (delta {p.delta():+d})")
        print(f"Total ABC delta: {total_delta:+d} bytes")

        if args.dry_run:
            return 0

        backup = ensure_backup(args.swf_path)
        print(f"Backup: {backup}")

        body_mut = bytearray(ctx.body)
        applied_delta = apply_patches(body_mut, all_patches)
        if applied_delta != total_delta:
            raise PatchError(
                f"Internal delta mismatch (expected {total_delta}, got {applied_delta})"
            )

        write_swf(ctx, body_mut, applied_delta)
        print("Patch apply complete.")
        return 0

    except PatchError as exc:
        print(f"Patch error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
