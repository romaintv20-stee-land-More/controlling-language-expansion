#!/usr/bin/env python3
"""Static QA for the single Marathi 1.0.1 Controlling + Minecraft 26.3 JAR."""
from __future__ import annotations
import argparse
import hashlib
import json
import unicodedata
import zipfile
from pathlib import Path

from build_marathi_1_0_1 import (
    BASE_SHA256,CONTROLLING,CONTROLLING_EN,DEFAULT_BASE,MOD_FILENAME,
    OUT,PROVENANCE,ROOT,VANILLA,jload
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
    controlling_entry="assets/controlling/lang/mr_in.json"
    minecraft_entry="assets/minecraft/lang/mr_in.json"
    added={controlling_entry,minecraft_entry}
    if set(candidate)!=set(source)|added:
        raise ValueError("All-in-one JAR changed/removes/adds unexpected archive entries")
    if any(candidate[n]!=old for n,old in source.items() if n!="pack.mcmeta"):
        raise ValueError("An original JAR entry changed; preserve all classes, loaders and locales")
    if json.loads(candidate[controlling_entry])!=controlling:
        raise ValueError("New Controlling Marathi entry differs from translation source")
    if json.loads(candidate[minecraft_entry])!=vanilla:
        raise ValueError("Embedded Minecraft Marathi language differs from 8559-key source")
    locales=[n for n in candidate if n.startswith("assets/controlling/lang/") and n.endswith(".json")]
    if len(locales)!=127:
        raise ValueError(f"Expected 127 Controlling locale files, got {len(locales)}")
    for meta in ("fabric.mod.json","META-INF/mods.toml","META-INF/neoforge.mods.toml"):
        if meta not in candidate or source[meta]!=candidate[meta]:
            raise ValueError(f"Original multi-loader metadata changed: {meta}")
    if json.loads(candidate["fabric.mod.json"])["version"]!="1.0.1":
        raise ValueError("Candidate Fabric metadata is not 1.0.1")
    original_meta=json.loads(source["pack.mcmeta"])
    metadata=json.loads(candidate["pack.mcmeta"])
    if metadata.get("pack")!=original_meta.get("pack"):
        raise ValueError("Embedded pack must preserve original Minecraft 1.21.9–26.3 format range")
    if metadata["pack"]["min_format"]!=[69,0] or metadata["pack"]["max_format"]!=[97,1]:
        raise ValueError("Expected original resource pack format range 69.0–97.1")
    if metadata["language"]!={"mr_in":{"name":"मराठी","region":"भारत","bidirectional":False}}:
        raise ValueError("Single JAR has no Marathi entry for Minecraft's language selector")
    hashes=jload(outdir/"marathi_1_0_1_SHA256.json")
    jar=outdir/MOD_FILENAME
    if (hashes["all_in_one_jar"]["sha256"]!=hashlib.sha256(jar.read_bytes()).hexdigest()
            or hashes["embedded_minecraft_language"] is not True
            or hashes["separate_zip_required"] is not False):
        raise ValueError("All-in-one candidate SHA-256 or embedded language metadata mismatch")
    frozen=ROOT/"release-candidates/1.0.1"
    if frozen.is_dir() and (frozen/MOD_FILENAME).exists():
        fixed=jload(frozen/"marathi_1_0_1_SHA256.json")
        final_jar=frozen/MOD_FILENAME
        if hashlib.sha256(final_jar.read_bytes()).hexdigest()!=fixed["all_in_one_jar"]["sha256"]:
            raise ValueError("Frozen single-JAR candidate digest mismatch")
        if get_info(final_jar)!=candidate:
            raise ValueError("Frozen single-JAR candidate stale against deterministic rebuild")
        print("PASS: committed single JAR matches a clean rebuild, entry by entry")
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
    print("PASS: one JAR embeds 8559 Minecraft keys, custom Marathi language metadata, archive integrity and SHA-256")
    print("NOTE: 722 machine-assisted entries need native review; in-game tests still required")
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base-jar",type=Path,default=DEFAULT_BASE)
    p.add_argument("--candidates",type=Path,default=OUT)
    p.add_argument("--official-english",type=Path)
    args=p.parse_args()
    print(json.dumps(audit(args.base_jar,args.candidates,args.official_english),ensure_ascii=False,indent=2))
