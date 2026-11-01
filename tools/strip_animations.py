#!/usr/bin/env python3
"""Create a copy of a Bedrock resource pack with client entity animations disabled."""
from __future__ import annotations
import argparse
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


def strip_json_comments(source: str) -> str:
    """Remove // and /* */ comments without touching quoted strings."""
    out = []
    i = 0
    in_string = False
    escaped = False
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if in_string:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
        elif ch == "/" and nxt == "/":
            i += 2
            while i < len(source) and source[i] not in "\r\n":
                i += 1
        elif ch == "/" and nxt == "*":
            i += 2
            while i + 1 < len(source) and source[i:i + 2] != "*/":
                i += 1
            i = min(len(source), i + 2)
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def remove_trailing_commas(source: str) -> str:
    out = []
    i = 0
    in_string = False
    escaped = False
    while i < len(source):
        ch = source[i]
        if in_string:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
        elif ch == ",":
            j = i + 1
            while j < len(source) and source[j].isspace():
                j += 1
            if j < len(source) and source[j] in "]}":
                i += 1
            else:
                out.append(ch)
                i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def disable_description_animations(description: Any) -> bool:
    if not isinstance(description, dict):
        return False
    changed = False
    # Keep render controllers, geometry and materials; remove animation aliases.
    if "animations" in description:
        del description["animations"]
        changed = True
    scripts = description.get("scripts")
    if isinstance(scripts, dict) and "animate" in scripts:
        del scripts["animate"]
        changed = True
        if not scripts:
            del description["scripts"]
    return changed


def disable_entity_animations(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    changed = False
    for component_key in ("minecraft:client_entity", "minecraft:attachable"):
        component = data.get(component_key)
        if isinstance(component, dict):
            changed = disable_description_animations(component.get("description")) or changed
    return changed


def make_mcpack(folder: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for file in sorted(folder.rglob("*")):
            if file.is_file():
                archive.write(file, file.relative_to(folder).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser(description="Tắt animation của client entities trong Bedrock Resource Pack")
    parser.add_argument("input", type=Path, help="Thư mục Resource Pack hoặc file .mcpack/.zip")
    parser.add_argument("--output", type=Path, help="Thư mục đầu ra; mặc định thêm _NoAnimations")
    parser.add_argument("--mcpack", action="store_true", help="Đóng gói kết quả thành file .mcpack")
    args = parser.parse_args()

    source_arg = args.input.expanduser().resolve()
    temp_obj = None
    source = source_arg
    if source_arg.is_file() and source_arg.suffix.lower() in {".mcpack", ".zip"}:
        temp_obj = tempfile.TemporaryDirectory(prefix="fixlagmcpe_")
        temp_root = Path(temp_obj.name).resolve()
        try:
            with zipfile.ZipFile(source_arg) as archive:
                for member in archive.infolist():
                    destination = (temp_root / member.filename).resolve()
                    if destination != temp_root and temp_root not in destination.parents:
                        continue
                    archive.extract(member, temp_root)
            candidates = list(temp_root.rglob("manifest.json"))
            if not candidates:
                raise ValueError("không tìm thấy manifest.json trong file pack")
            source = next((item.parent for item in candidates if item.parent == temp_root), candidates[0].parent)
        except (OSError, zipfile.BadZipFile, ValueError) as exc:
            temp_obj.cleanup()
            print(f"Lỗi đọc pack: {exc}", file=sys.stderr)
            return 2
    elif not source_arg.is_dir():
        print("Lỗi: đầu vào phải là thư mục Resource Pack hoặc file .mcpack/.zip", file=sys.stderr)
        return 2

    if not (source / "manifest.json").is_file():
        if temp_obj:
            temp_obj.cleanup()
        print("Lỗi: không tìm thấy manifest.json ở thư mục gốc của pack", file=sys.stderr)
        return 2
    default_name = source_arg.stem + "_NoAnimations" if source_arg.is_file() else source_arg.name + "_NoAnimations"
    output = (args.output or source_arg.with_name(default_name)).expanduser().resolve()
    if output == source or source in output.parents:
        if temp_obj:
            temp_obj.cleanup()
        print("Lỗi: thư mục đầu ra không được nằm trong thư mục gốc của pack", file=sys.stderr)
        return 2
    if output.exists():
        if temp_obj:
            temp_obj.cleanup()
        print(f"Lỗi: đầu ra đã tồn tại: {output}\nHãy đổi --output hoặc xóa thư mục cũ.", file=sys.stderr)
        return 2

    try:
        shutil.copytree(source, output)
        scanned = changed = skipped = 0
        for json_file in output.rglob("*.json"):
            try:
                raw = json_file.read_text(encoding="utf-8-sig")
                cleaned = remove_trailing_commas(strip_json_comments(raw))
                data = json.loads(cleaned)
                scanned += 1
                if disable_entity_animations(data):
                    json_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    changed += 1
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                skipped += 1
                print(f"Bỏ qua {json_file.relative_to(output)}: {exc}")

        print(f"Đã quét {scanned} JSON; sửa {changed} file; bỏ qua {skipped} file lỗi.")
        print(f"Pack không animation: {output}")
        if args.mcpack:
            mcpack = output.with_suffix(".mcpack")
            make_mcpack(output, mcpack)
            print(f"Đã tạo: {mcpack}")
        print("Lưu ý: chỉ tắt animation được khai báo trong client entity/attachable; animation bên ngoài hoặc behavior script có thể còn lại.")
        return 0
    finally:
        if temp_obj:
            temp_obj.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
