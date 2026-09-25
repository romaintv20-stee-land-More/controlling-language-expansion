#!/usr/bin/env python3
"""Validate 26.3.3 localization against the published 26.3 addon baseline."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data/upstream_release_26_3_audit.json"
CANONICAL = ROOT / "data/canonical_english.json"
LANG_DIR = "common/src/main/resources/assets/controlling/lang"
UPSTREAM = "https://github.com/Jaredlll08/Controlling.git"

def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args],
                            capture_output=True, text=True, encoding="utf-8", check=True)
    return result.stdout

def verify_repo(repo: Path, audit: dict) -> None:
    actual = {}
    for line in git(repo, "ls-tree", "-r", "HEAD", "--", LANG_DIR).splitlines():
        metadata, path = line.split("\t", 1)
        if path.endswith(".json"):
            actual[path] = metadata.split()[2]
    expected = audit["upstream"]["official_locale_git_blob_shas"]
    if actual != expected:
        added = sorted(actual.keys() - expected.keys())
        removed = sorted(expected.keys() - actual.keys())
        changed = sorted(k for k in expected.keys() & actual.keys() if expected[k] != actual[k])
        raise ValueError(f"Controlling upstream localization changed: added={added}, "
                         f"removed={removed}, changed={changed}; re-audit before release")
    properties = git(repo, "show", "HEAD:gradle.properties")
    for prop in ("minecraft=26.3", "java_version=25", "mod_version=26.3"):
        if prop not in properties.splitlines():
            raise ValueError(f"Unexpected Controlling 26.3 build property: {prop}")
    upstream_en = json.loads(git(repo, "show", f"HEAD:{LANG_DIR}/en_us.json"))
    canon = json.loads(CANONICAL.read_text(encoding="utf-8"))
    if len(upstream_en) != 12 or any(canon.get(k) != v for k, v in upstream_en.items()):
        raise ValueError("Published generation 07 has new or changed English keys")
    print("PASS: upstream Controlling 26.3 language blobs unchanged from 26.3.1 to current branch")
    print(f"PASS: {len(actual)} official JSON locale files and {len(upstream_en)} English keys; Java 25")

def verify_binary(repo: Path, audit: dict, jar: Path) -> None:
    published = audit["addon_public_file"]
    data = jar.read_bytes()
    if len(data) != published["published_jar_bytes"] or hashlib.sha256(data).hexdigest() != published["published_jar_sha256"]:
        raise ValueError("The supplied JAR does not match the published 1.0.1 file")
    upstream_en = json.loads(git(repo, "show", f"HEAD:{LANG_DIR}/en_us.json"))
    with zipfile.ZipFile(jar) as z:
        if z.testzip() is not None:
            raise ValueError("Published JAR archive failed CRC integrity validation")
        names = z.namelist()
        translations = [name for name in names
                        if name.startswith("assets/controlling/lang/") and name.endswith(".json")]
        if len(translations) != published["jar_locale_file_count"]:
            raise ValueError(f"Published JAR language count changed: {len(translations)}")
        pack = json.loads(z.read("pack.mcmeta"))["pack"]
        if pack["min_format"] != published["resource_pack_min_format"] or pack["max_format"] != published["resource_pack_max_format"]:
            raise ValueError("Published JAR has unexpected Minecraft resource pack compatibility range")
        fabric = json.loads(z.read("fabric.mod.json"))
        if fabric["version"] != published["version"] or fabric["id"] != "controllinglanguageexpansion":
            raise ValueError("Published Fabric metadata does not match 1.0.1 addon")
        if "META-INF/neoforge.mods.toml" not in names or "META-INF/mods.toml" not in names:
            raise ValueError("Published JAR is missing NeoForge or Forge metadata")
        official = {Path(p).stem for p in audit["upstream"]["official_locale_git_blob_shas"]}
        overlaps = {}
        for item in translations:
            locale = Path(item).stem
            payload = json.loads(z.read(item))
            if not set(payload) <= set(upstream_en):
                raise ValueError(f"{locale}: addon contains keys absent from Controlling 26.3")
            if locale in official:
                original = json.loads(git(repo, "show", f"HEAD:{LANG_DIR}/{locale}.json"))
                collision = set(payload) & set(original)
                if collision:
                    overlaps[locale] = sorted(collision)
        if overlaps:
            raise ValueError(f"Published addon overlaps official upstream translations: {overlaps}")
    print(f"PASS: published {published['version']} JAR has {len(translations)} files; no official translation overlaps")
    print("PASS: JAR CRC, Forge/NeoForge/Fabric metadata and resource pack format 69.0–97.1")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jar", type=Path, help="Optional copy of the released CurseForge JAR")
    args = parser.parse_args()
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="controlling-26.3-release-") as temp:
        checkout = Path(temp) / "upstream"
        subprocess.run(["git", "clone", "--quiet", "--depth", "1", "--branch", "26.3",
                        "--filter=blob:none", UPSTREAM, str(checkout)], check=True)
        verify_repo(checkout, audit)
        if args.jar:
            verify_binary(checkout, audit, args.jar)
    print("PASS: no localization-only rebuild necessary for Controlling 26.3.3")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
