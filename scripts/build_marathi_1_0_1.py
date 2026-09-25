#!/usr/bin/env python3
"""Build a single Controlling Language Expansion 1.0.1 JAR containing both Marathi
Controlling strings and the embedded Minecraft 26.3 Marathi language pack.
Retain the original 126 locales and all compiled loader classes.
Static candidate only: no automatic public release without in-game tests.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA256="853cd6b5435f82f8bce6e67ee6595cbc3e19b9616ec14fa33a9f1eb0c36cfc64"
DEFAULT_BASE=ROOT/"vendor/Controlling-Language-Expansion-1.0.1-original.jar"
CONTROLLING=ROOT/"translations/modern/mr_in.json"
VANILLA=ROOT/"translations/minecraft/26.3/mr_in.json"
PROVENANCE=ROOT/"translations/minecraft/26.3/provenance.json"
OUT=ROOT/"build/candidates"
MOD_FILENAME="Controlling-Language-Expansion-1.0.1-mc1.21.9-26.3-marathi-all-in-one.jar"
CONTROLLING_EN={
    "options.showAll":"Show All","options.showConflicts":"Show Conflicts",
    "options.showNone":"Show Unbound","options.availableKeys":"Available Keys",
    "options.sort":"Sort","options.sortNone":"None",
    "options.sortAZ":"A->Z","options.sortZA":"Z->A",
    "options.sortKeyAZ":"Key A->Z","options.sortKeyZA":"Key Z->A",
    "options.toggleFree":"Toggle Free","options.confirmReset":"Confirm?",
}
LANGUAGE={"mr_in":{"name":"मराठी","region":"भारत","bidirectional":False}}
ZIP_DATE=(2026,9,25,0,0,0)

def jload(path:Path)->dict:
    return json.loads(path.read_text(encoding="utf-8"))

def add(zf:zipfile.ZipFile,name:str,content:bytes)->None:
    info=zipfile.ZipInfo(name,date_time=ZIP_DATE)
    info.compress_type=zipfile.ZIP_DEFLATED
    info.external_attr=0o644<<16
    zf.writestr(info,content,compresslevel=9)

def encoded(data:dict)->bytes:
    return (json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode("utf-8")

def build(base:Path,output:Path)->dict:
    if not base.is_file():
        raise FileNotFoundError(f"Pinned 1.0.1 baseline JAR missing: {base}")
    actual=hashlib.sha256(base.read_bytes()).hexdigest()
    if actual!=BASE_SHA256:
        raise ValueError(f"Unrecognized 1.0.1 baseline JAR SHA-256: {actual}")
    ctrl=jload(CONTROLLING)
    if set(ctrl)!=set(CONTROLLING_EN) or not all(isinstance(v,str) and v.strip() for v in ctrl.values()):
        raise ValueError("Marathi Controlling translations must cover exactly the 12 upstream keys")
    vanilla=jload(VANILLA)
    provenance=jload(PROVENANCE)
    if len(vanilla)!=8559 or provenance["official_target_english_keys"]!=8559 or vanilla.get("language.code")!="mr_in":
        raise ValueError("Minecraft 26.3 Marathi translation is incomplete or wrong locale")
    output.mkdir(parents=True,exist_ok=True)
    jar=output/MOD_FILENAME
    entry="assets/controlling/lang/mr_in.json"
    minecraft_entry="assets/minecraft/lang/mr_in.json"
    with zipfile.ZipFile(base) as inp, zipfile.ZipFile(jar,"w") as out:
        files=inp.namelist()
        original={n:inp.read(n) for n in files}
        if (inp.testzip() is not None or len(files)!=len(set(files))
                or entry in files or minecraft_entry in files):
            raise ValueError("Baseline 1.0.1 archive invalid or already contains Marathi")
        if not all(n in files for n in ("fabric.mod.json","META-INF/neoforge.mods.toml",
                                        "META-INF/mods.toml","pack.mcmeta")):
            raise ValueError("Baseline JAR lost multi-loader metadata")
        original_pack=json.loads(original["pack.mcmeta"])
        existing_range=original_pack.get("pack",{})
        if existing_range.get("max_format")!=[97,1] or existing_range.get("min_format")!=[69,0]:
            raise ValueError("Original 1.0.1 resource pack compatibility range changed")
        declared=original_pack.setdefault("language",{})
        if "mr_in" in declared and declared["mr_in"]!=LANGUAGE["mr_in"]:
            raise ValueError("Conflicting Marathi language declaration in original JAR")
        declared.update(LANGUAGE)
        old_langs=[p for p in files if p.startswith("assets/controlling/lang/") and p.endswith(".json")]
        if len(old_langs)!=126 or any(p.endswith("/mr_in.json") for p in old_langs):
            raise ValueError("Unexpected baseline locale set")
        for info in inp.infolist():
            # Preserve each original entry, including every class and loader descriptor,
            # except pack.mcmeta, which needs the custom Minecraft language declaration.
            payload=encoded(original_pack) if info.filename=="pack.mcmeta" else original[info.filename]
            out.writestr(info,payload)
        add(out,entry,encoded(ctrl))
        add(out,minecraft_entry,encoded(vanilla))
        out.comment=inp.comment
    result={
        "all_in_one_jar":{
            "filename":jar.name,
            "sha256":hashlib.sha256(jar.read_bytes()).hexdigest(),
            "size":jar.stat().st_size
        },
        "project_version":"1.0.1","minecraft":"26.3","locale":"mr_in",
        "mod_original_sha256":BASE_SHA256,"controlling_locale_count":127,
        "controlling_marathi_keys":12,"minecraft_marathi_keys":8559,
        "embedded_minecraft_language":True,"separate_zip_required":False,
        "release_status":"static_candidate; not published"
    }
    (output/"marathi_1_0_1_SHA256.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PASS: built one 1.0.1 JAR with Marathi Controlling + Minecraft 26.3 built in")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--base-jar",type=Path,default=DEFAULT_BASE)
    parser.add_argument("--out",type=Path,default=OUT)
    args=parser.parse_args()
    build(args.base_jar,args.out)
