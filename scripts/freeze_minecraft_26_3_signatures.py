#!/usr/bin/env python3
"""Freeze only official Minecraft 26.3 English key names/token signatures, not text."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from prepare_marathi_26_3 import TOKEN
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/minecraft_26_3_key_signatures.json"

def freeze(source:Path)->dict:
    data=json.loads(source.read_text(encoding="utf-8"))
    if len(data)!=8559:
        raise ValueError(f"Expected 8559 official Minecraft 26.3 keys, got {len(data)}")
    tokenized={k:sorted(TOKEN.findall(v)) for k,v in sorted(data.items()) if TOKEN.search(v)}
    return {
        "schema_version":1,"minecraft":"26.3",
        "source":"Official Minecraft 26.3 client JAR assets/minecraft/lang/en_us.json",
        "english_source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
        "official_key_count":len(data),"keys":sorted(data),
        "empty_value_keys":sorted(k for k,v in data.items() if not v),
        "technical_token_signatures":tokenized,
    }
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--english",type=Path,required=True)
    args=parser.parse_args()
    out=freeze(args.english)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PASS: frozen",out["official_key_count"],"official 26.3 keys and",len(out["technical_token_signatures"]),"technical-token signatures")
    print("English source SHA256:",out["english_source_sha256"])
