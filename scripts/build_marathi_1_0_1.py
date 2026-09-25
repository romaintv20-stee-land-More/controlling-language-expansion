#!/usr/bin/env python3
"""Build Controlling Language Expansion 1.0.1 + standalone Minecraft 26.3 Marathi pack.

Use the user's pinned 1.0.1 baseline JAR, retaining all original loader classes and
126 locale files. Do not change the original artifact or promote without in-game tests.
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
MOD_FILENAME="Controlling-Language-Expansion-1.0.1-mc1.21.9-26.3-marathi.jar"
PACK_FILENAME="Minecraft-26.3-Marathi-mr_in-1.0.1.zip"
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
    with zipfile.ZipFile(base) as inp, zipfile.ZipFile(jar,"w") as out:
        files=inp.namelist()
        original={n:inp.read(n) for n in files}
        if inp.testzip() is not None or len(files)!=len(set(files)) or entry in files:
            raise ValueError("Baseline 1.0.1 archive invalid or already contains Marathi")
        if not all(n in files for n in ("fabric.mod.json","META-INF/neoforge.mods.toml","META-INF/mods.toml","pack.mcmeta")):
            raise ValueError("Baseline JAR lost multi-loader metadata")
        old_langs=[p for p in files if p.startswith("assets/controlling/lang/") and p.endswith(".json")]
        if len(old_langs)!=126 or any(p.endswith("/mr_in.json") for p in old_langs):
            raise ValueError("Unexpected baseline locale set")
        for info in inp.infolist():
            out.writestr(info,original[info.filename])
        add(out,entry,encoded(ctrl))
        out.comment=inp.comment
    pack=output/PACK_FILENAME
    pack_meta={
        "pack":{"description":"मराठी • Minecraft 26.3 • Beyond & More translations",
                "min_format":[97,1],"max_format":[97,1]},
        "language":LANGUAGE,
    }
    with zipfile.ZipFile(pack,"w") as zf:
        add(zf,"pack.mcmeta",encoded(pack_meta))
        add(zf,"assets/minecraft/lang/mr_in.json",encoded(vanilla))
        add(zf,"README.txt",(
            "Minecraft 26.3 Marathi language pack (mr_in)\n"
            "Place this ZIP in .minecraft/resourcepacks, enable it in Minecraft, "
            "then select Marathi in Language settings.\n"
            "Install Controlling Language Expansion 1.0.1 separately for Controlling's 12 Marathi strings.\n"
            "Translations reuse Beyond & More 26.1.2 wherever the English key/meaning is unchanged. "
            "New or modified lines use machine-assisted Marathi and need native-speaker review.\n"
        ).encode("utf-8"))
    result={}
    for name,p in (("controlling_jar",jar),("minecraft_26_3_resourcepack",pack)):
        result[name]={"filename":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"size":p.stat().st_size}
    result.update({"project_version":"1.0.1","minecraft":"26.3","locale":"mr_in",
                   "mod_original_sha256":BASE_SHA256,"controlling_locale_count":127,
                   "controlling_marathi_keys":12,"minecraft_marathi_keys":8559,
                   "release_status":"static_candidate; not published"})
    (output/"marathi_1_0_1_SHA256.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PASS: built Marathi Controlling 1.0.1 candidate and Minecraft 26.3 language pack")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--base-jar",type=Path,default=DEFAULT_BASE)
    parser.add_argument("--out",type=Path,default=OUT)
    args=parser.parse_args()
    build(args.base_jar,args.out)
