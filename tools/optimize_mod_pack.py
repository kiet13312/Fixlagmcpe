#!/usr/bin/env python3
"""Tạo bản Resource Pack Bedrock nhẹ hơn từ pack gốc."""
from __future__ import annotations
import argparse, json, shutil, sys, tempfile, zipfile
from pathlib import Path

def strip_comments(s):
    out=[]; i=0; quote=False; esc=False
    while i<len(s):
        c=s[i]; n=s[i+1] if i+1<len(s) else ""
        if quote:
            out.append(c)
            if esc: esc=False
            elif c=="\\": esc=True
            elif c=='"': quote=False
            i+=1; continue
        if c=='"': quote=True; out.append(c); i+=1
        elif c=="/" and n=="/":
            i+=2
            while i<len(s) and s[i] not in "\r\n": i+=1
        elif c=="/" and n=="*":
            i+=2
            while i+1<len(s) and s[i:i+2]!="*/": i+=1
            i=min(len(s),i+2)
        else: out.append(c); i+=1
    return "".join(out)

def remove_trailing_commas(s):
    out=[]; i=0; quote=False; esc=False
    while i<len(s):
        c=s[i]
        if quote:
            out.append(c)
            if esc: esc=False
            elif c=="\\": esc=True
            elif c=='"': quote=False
            i+=1; continue
        if c=='"': quote=True; out.append(c); i+=1
        elif c==",":
            j=i+1
            while j<len(s) and s[j].isspace(): j+=1
            if j<len(s) and s[j] in "]}": i+=1
            else: out.append(c); i+=1
        else: out.append(c); i+=1
    return "".join(out)

def safe_extract(src,dst):
    with zipfile.ZipFile(src) as z:
        for item in z.infolist():
            target=(dst/item.filename).resolve()
            if target!=dst.resolve() and dst.resolve() not in target.parents:
                raise ValueError(f"unsafe zip path: {item.filename}")
            z.extract(item,dst)

def zip_pack(folder,out):
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=8) as z:
        for f in sorted(folder.rglob("*")):
            if f.is_file(): z.write(f,f.relative_to(folder).as_posix())
    with zipfile.ZipFile(out) as z:
        if z.testzip(): raise RuntimeError("generated mcpack is corrupt")

def main():
    ap=argparse.ArgumentParser(description="Optimize a Bedrock Resource Pack")
    ap.add_argument("input",type=Path,help="resource-pack folder or .mcpack/.zip")
    ap.add_argument("--output",type=Path)
    ap.add_argument("--mcpack",action="store_true")
    ap.add_argument("--max-texture",type=int,default=128)
    ap.add_argument("--brighten-blocks",type=float,default=1.06)
    ap.add_argument("--remove-particles",action="store_true")
    args=ap.parse_args()
    src=args.input.expanduser().resolve(); temp=None
    if src.is_file() and src.suffix.lower() in (".mcpack",".zip"):
        temp=tempfile.TemporaryDirectory(prefix="fixlagmcpe_")
        root=Path(temp.name)
        try: safe_extract(src,root)
        except (OSError,zipfile.BadZipFile,ValueError) as e:
            temp.cleanup(); print(f"Extract failed: {e}",file=sys.stderr); return 2
        manifests=list(root.rglob("manifest.json"))
        if not manifests:
            temp.cleanup(); print("manifest.json not found",file=sys.stderr); return 2
        source=next((p.parent for p in manifests if p.parent==root),manifests[0].parent)
    elif src.is_dir(): source=src
    else: print("Input must be a folder, .mcpack or .zip",file=sys.stderr); return 2
    if not (source/"manifest.json").is_file():
        if temp: temp.cleanup()
        print("manifest.json must be at pack root",file=sys.stderr); return 2
    out=(args.output or src.with_name(src.stem+"_Lite" if src.is_file() else src.name+"_Lite")).expanduser().resolve()
    if out.exists() or out==source or source in out.parents:
        if temp: temp.cleanup()
        print(f"Invalid or existing output: {out}",file=sys.stderr); return 2
    try:
        shutil.copytree(source,out)
        scanned=edited=skipped=0
        for jf in out.rglob("*.json"):
            try:
                data=json.loads(remove_trailing_commas(strip_comments(jf.read_text(encoding="utf-8-sig"))))
                scanned+=1; changed=False
                for key in ("minecraft:client_entity","minecraft:attachable"):
                    desc=data.get(key,{}).get("description",{}) if isinstance(data,dict) else {}
                    if isinstance(desc,dict):
                        if "animations" in desc: del desc["animations"]; changed=True
                        scripts=desc.get("scripts")
                        if isinstance(scripts,dict) and "animate" in scripts:
                            del scripts["animate"]; changed=True
                            if not scripts: del desc["scripts"]
                if changed:
                    jf.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); edited+=1
            except (OSError,UnicodeError,json.JSONDecodeError): skipped+=1
        for name in ("animations","animation_controllers"):
            for folder in list(out.rglob(name)):
                if folder.is_dir(): shutil.rmtree(folder)
        flip=out/"textures"/"flipbook_textures.json"
        if flip.parent.exists(): flip.write_text("[]\n",encoding="utf-8")
        if args.remove_particles:
            for folder in list(out.rglob("particles")):
                if folder.is_dir(): shutil.rmtree(folder)
        resized=brightened=0
        try:
            from PIL import Image,ImageEnhance
            for path in out.rglob("*.png"):
                try:
                    with Image.open(path) as im:
                        im=im.convert("RGBA")
                        if args.max_texture>0 and max(im.size)>args.max_texture:
                            im.thumbnail((args.max_texture,args.max_texture),Image.Resampling.LANCZOS); resized+=1
                        if "textures/blocks/" in path.as_posix() and args.brighten_blocks>1:
                            alpha=im.getchannel("A")
                            rgb=Image.merge("RGB",im.split()[:3])
                            rgb=ImageEnhance.Brightness(rgb).enhance(args.brighten_blocks)
                            im=Image.merge("RGBA",(*rgb.split(),alpha)); brightened+=1
                        im.save(path,optimize=True)
                except Exception as e: print(f"Skip image {path}: {e}")
        except ImportError: print("Pillow unavailable; image optimization skipped.")
        print(f"Scanned JSON: {scanned}; modified: {edited}; invalid JSON: {skipped}; resized PNG: {resized}; brightened block PNG: {brightened}")
        print(f"Output: {out}")
        if args.mcpack:
            packed=out.with_suffix(".mcpack"); zip_pack(out,packed); print(f"MCpack: {packed}")
        print("Note: behavior scripts and external scripts are not changed. Particle removal is optional.")
        return 0
    finally:
        if temp: temp.cleanup()

if __name__=="__main__": raise SystemExit(main())
