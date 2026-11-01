#!/usr/bin/env python3
"""Build the lightweight, bright, original BareBright-style Bedrock resource pack."""
from __future__ import annotations
import json
import struct
import zlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist"
PACK = OUT / "FixLagMCPE_BareBright"


def png_bytes(pixels):
    height, width = len(pixels), len(pixels[0])
    raw = b"".join(b"\x00" + b"".join(bytes(px) for px in row) for row in pixels)
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 6, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


PALETTES = {
    "stone": [(190,196,199,255),(211,216,215,255),(174,183,187,255),(225,229,224,255)],
    "dirt": [(165,116,76,255),(184,136,91,255),(147,99,66,255),(198,151,103,255)],
    "grass": [(104,190,75,255),(119,204,82,255),(91,174,66,255),(139,214,92,255)],
    "cobble": [(151,160,164,255),(181,190,191,255),(132,143,148,255),(205,210,205,255)],
    "sand": [(235,216,150,255),(246,229,169,255),(224,203,132,255),(252,237,185,255)],
    "wood": [(205,160,103,255),(222,181,123,255),(187,139,85,255),(235,196,139,255)],
    "leaves": [(79,161,76,255),(100,184,83,255),(61,143,67,255),(126,199,94,255)],
}


def make_tile(kind):
    p = PALETTES[kind]
    grid = [[p[0] for _ in range(16)] for _ in range(16)]
    for y in range(16):
        for x in range(16):
            if kind == "stone":
                idx = (x * 3 + y * 5 + x // 4) % 4
            elif kind == "cobble":
                idx = ((x // 4) + (y // 4) * 2 + int(x % 3 == 0)) % 4
            elif kind == "wood":
                idx = (y // 4 + int(x % 7 == 0)) % 4
            else:
                idx = (x * 7 + y * 11 + (x * y) % 5) % 4
            grid[y][x] = p[idx]
    if kind == "cobble":
        for y in (3, 7, 11):
            for x in range(16):
                grid[y][x] = p[2]
    if kind == "wood":
        for y in (3, 7, 11):
            for x in range(16):
                grid[y][x] = p[2]
    return grid


def main():
    textures = PACK / "textures" / "blocks"
    textures.mkdir(parents=True, exist_ok=True)
    manifest = {
        "format_version": 2,
        "header": {
            "name": "FixLagMCPE - BareBright",
            "description": "Texture 16x16 sáng, gọn và tối giản cho Minecraft Bedrock.",
            "uuid": "5e46c082-8bf4-5c8f-8b80-19d3f06a1b11",
            "version": [1, 0, 0],
            "min_engine_version": [1, 21, 0]
        },
        "modules": [{
            "type": "resources",
            "uuid": "f0a0f32a-e46f-5b26-b8d1-4c9792ce047c",
            "version": [1, 0, 0]
        }]
    }
    PACK.mkdir(parents=True, exist_ok=True)
    (PACK / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    block_names = {
        "stone": "stone", "dirt": "dirt", "grass_top": "grass",
        "cobblestone": "cobble", "sand": "sand", "planks_oak": "wood",
        "leaves_oak": "leaves"
    }
    for filename, kind in block_names.items():
        (textures / f"{filename}.png").write_bytes(png_bytes(make_tile(kind)))
    icon = [[(95,187,87,255) if (x+y)%5 else (245,223,158,255) for x in range(64)] for y in range(64)]
    (PACK / "pack_icon.png").write_bytes(png_bytes(icon))
    mcpack = OUT / "FixLagMCPE_BareBright.mcpack"
    with zipfile.ZipFile(mcpack, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for file in sorted(PACK.rglob("*")):
            if file.is_file():
                archive.write(file, file.relative_to(PACK).as_posix())
    print(mcpack)


if __name__ == "__main__":
    main()
