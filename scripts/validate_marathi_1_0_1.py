#!/usr/bin/env python3
"""Static QA for the Marathi Controlling 1.0.1 JAR and Minecraft 26.3 pack."""
from __future__ import annotations
import argparse
import hashlib
import json
import unicodedata
import zipfile
from pathlib import Path

from build_marathi_1_0_1 import (
    BASE_SHA256,CONTROLLING,CONTROLLING_EN,DEFAULT_BASE,MOD_FILENAME,
    OUT,PACK_FILENAME,PROVENANCE,ROOT,VANILLA,jload
)
from prepare_marathi_26_3 import TOKEN

SIGNATURES=ROOT/"data/minecraft_26_3_key_signatures.json"
UPSTREAM_AUDIT=ROOT/"data/upstream_release_26_3_audit.json"
SELECTED_LANG="mr_in"

def get_info(path:Path):
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:raise ValueError(f"Invalid ZIP CRC: {path}")
        names=z.namelist()
        if len(names)!=len(set(names)) or any(n.startswith("/") or ".." in Path(n).parts for n in names):
            raise ValueError(f"Duplicate or path-traversal ZIP members: {path}")
        return {n:z.read(n) for n in names}

def audit(base:Path,outdir:Path,english:Path|None)->dict:
    if hashlib.sha256(base.read_bytes()).hexdigest()!=BASE_SHA256:
        raise ValueError("Original JAR SHA-256 differs from pinned user-owned baseline")
    official=jload(SIGNATURES)
    provenance=jload(PROVENANCE)
    vanilla=jload(VANILLA)
    controlling=jload(CONTROLLING)
    if len(official["keys"])!=8559 or set(official["keys"])!=set(vanilla):
        raise ValueError("Minecraft Marathi keys do not match official 26.3 English key inventory")
    tokenized=official["technical_token_signatures"]
    empty_keys=set(official["empty_value_keys"])
    violations=[]
    for k,v in vanilla.items():
        if not isinstance(v,str) or (not v.strip() and k not in empty_keys):
            violations.append((k,"unexpected empty/non-string"))
            continue
        expected=tokenized.get(k,[])
        actual=sorted(TOKEN.findall(v))
        if expected!=actual:violations.append((k,expected,actual))
    if violations:
        raise ValueError(f"Corrupted Minecraft formatting/technical tokens: {violations[:15]}")
    if vanilla["language.code"]!="mr_in":
        raise ValueError("B&M English language.code fallback was not corrected to mr_in")
    if len(controlling)!=12 or set(controlling)!=set(CONTROLLING_EN):
        raise ValueError("Controlling Marathi translation has missing or invented keys")
    if not all(isinstance(v,str) and v.strip() for v in controlling.values()):
        raise ValueError("Controlling Marathi contains an empty value")
    if english:
        data=jload(english)
        if set(data)!=set(vanilla) or hashlib.sha256(english.read_bytes()).hexdigest()!=official["english_source_sha256"]:
            raise ValueError("Local English file is not official Minecraft 26.3 reference")
    methods=provenance["translation_methods"]
    if (methods["beyond_same_key_same_english"],methods["beyond_same_english_other_key"],methods["curated"],methods["machine_google"])!=(7790,45,2,722):
        raise ValueError("Marathi provenance counts are stale")
    if sum(methods.values())!=8559 or provenance["machine_translation_requires_native_speaker_review"] is not True:
        raise ValueError("Marathi completeness or review status inconsistent")
    upstream=jload(UPSTREAM_AUDIT)
    official_locales={Path(path).stem for path in upstream["upstream"]["official_locale_git_blob_shas"]}
    if SELECTED_LANG in official_locales or len(official_locales)!=24:
        raise ValueError("Marathi locale now exists in Controlling upstream; re-audit ownership")
    source=get_info(base)
    candidate=get_info(outdir/MOD_FILENAME)
    new_entry="assets/controlling/lang/mr_in.json"
    if set(candidate)!=set(source)|{new_entry}:
        raise ValueError("Candidate JAR changed/removes/adds unexpected members")
    if any(candidate[n]!=v for n,v in source.items()):
        raise ValueError("An existing original JAR entry changed; preserve other languages and loaders")
    if json.loads(candidate[new_entry])!=controlling:
        raise ValueError("New Marathi entry differs from reviewed Controlling translation source")
    all_locale=[n for n in candidate if n.startswith("assets/controlling/lang/") and n.endswith(".json")]
    if len(all_locale)!=127 or not all(meta in candidate for meta in ("fabric.mod.json","META-INF/mods.toml","META-INF/neoforge.mods.toml")):
        raise ValueError("Candidate missing multi-loader metadata or expected 127 locales")
    if json.loads(candidate["fabric.mod.json"])["version"]!="1.0.1":
        raise ValueError("Candidate Fabric metadata is not 1.0.1")
    pack=get_info(outdir/PACK_FILENAME)
    if "assets/minecraft/lang/mr_in.json" not in pack or "pack.mcmeta" not in pack:
        raise ValueError("Minecraft Marathi resource pack missing required assets")
    if json.loads(pack["assets/minecraft/lang/mr_in.json"])!=vanilla:
        raise ValueError("Resource pack translation differs from source")
    metadata=json.loads(pack["pack.mcmeta"])
    if metadata["pack"]["min_format"]!=[97,1] or metadata["pack"]["max_format"]!=[97,1]:
        raise ValueError("Resource pack does not target official Minecraft 26.3 format 97.1")
    if metadata["language"]!={"mr_in":{"name":"मराठी","region":"भारत","bidirectional":False}}:
        raise ValueError("Minecraft custom Marathi language declaration missing")
    hashes=jload(outdir/"marathi_1_0_1_SHA256.json")
    for typ,path in (("controlling_jar",outdir/MOD_FILENAME),("minecraft_26_3_resourcepack",outdir/PACK_FILENAME)):
        if hashes[typ]["sha256"]!=hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError(f"{typ}: pinned candidate digest mismatch")
    frozen=ROOT/"release-candidates/1.0.1"
    if frozen.is_dir():
        fixed=jload(frozen/"marathi_1_0_1_SHA256.json")
        for label,filename in (("controlling_jar",MOD_FILENAME),("minecraft_26_3_resourcepack",PACK_FILENAME)):
            candidate_file=frozen/filename
            if hashlib.sha256(candidate_file.read_bytes()).hexdigest()!=fixed[label]["sha256"]:
                raise ValueError(f"Frozen {label} has invalid SHA-256")
            if get_info(candidate_file)!=get_info(outdir/filename):
                raise ValueError(f"Frozen {label} has stale ZIP contents compared to reconstructed build")
        print("PASS: frozen JAR and resource-pack candidates match the rebuilt source byte-for-byte per entry")
    result={
        "minecraft":"26.3","pack_format":"97.1",
        "minecraft_keys":len(vanilla),"placeholder_signature_keys":len(tokenized),
        "marathi_mod_keys":len(controlling),"preserved_original_jar_entries":len(source),
        "total_controlling_locales":127,
        "remaining_unchanged_english_values":provenance["remaining_english_values"],
        "machine_assisted_text_review_required":True,
        "in_game_test_completed":False,
    }
    print("PASS: Marathi Minecraft 26.3 key and 1082 token-signature QA")
    print("PASS: 12 Marathi Controlling keys, all 126 original locale files preserved, all loader metadata preserved")
    print("PASS: 8559-key resource pack, 97.1 metadata, user-visible Marathi selector, archive integrity and SHA-256")
    print("NOTE: 722 machine-assisted entries need native review; in-game tests still required")
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base-jar",type=Path,default=DEFAULT_BASE)
    p.add_argument("--candidates",type=Path,default=OUT)
    p.add_argument("--official-english",type=Path)
    args=p.parse_args()
    print(json.dumps(audit(args.base_jar,args.candidates,args.official_english),ensure_ascii=False,indent=2))
