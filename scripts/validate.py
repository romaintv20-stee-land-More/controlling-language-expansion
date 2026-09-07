#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "data" / "project_policy.json"
CANONICAL_ENGLISH = ROOT / "data" / "canonical_english.json"
LEGACY_BUNDLE = ROOT / "translations" / "legacy_01.json"
LEGACY_SOURCES = ROOT / "data" / "legacy_locale_sources.json"
LOCALE_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)?$")
LEGACY_KEYS = {
    "options.search",
    "options.showAll",
    "options.showConflicts",
    "options.showNone",
    "options.availableKeys",
    "options.sort",
    "options.category",
    "options.key",
    "options.sortNone",
    "options.sortAZ",
    "options.sortZA",
    "options.toggleFree",
    "options.confirmReset",
}

def load_json_unique(path: Path):
    def hook(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError(f"{path}: duplicate key {key!r}")
            out[key] = value
        return out
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=hook)

def validate_policy():
    data = load_json_unique(POLICY)
    required = {"project_version", "minecraft_min", "minecraft_max", "locale_policy", "official_upstream_priority", "upstream_repository", "release_status"}
    missing = sorted(required - set(data))
    if missing:
        raise ValueError(f"{POLICY}: missing fields: {', '.join(missing)}")
    if data["official_upstream_priority"] is not True:
        raise ValueError("Official upstream priority must remain enabled")

def validate_legacy_bundle():
    english = load_json_unique(CANONICAL_ENGLISH)
    if not LEGACY_KEYS <= set(english):
        raise ValueError("Canonical English is missing legacy keys")
    bundle = load_json_unique(LEGACY_BUNDLE)
    if bundle.get("pack") != "legacy_01" or not isinstance(bundle.get("translations"), dict):
        raise ValueError(f"{LEGACY_BUNDLE}: invalid structure")
    entries = 0
    for locale, data in bundle["translations"].items():
        if not LOCALE_RE.fullmatch(locale):
            raise ValueError(f"{LEGACY_BUNDLE}: invalid locale {locale}")
        if not isinstance(data, dict):
            raise ValueError(f"{LEGACY_BUNDLE}: locale {locale} must map to an object")
        unknown = sorted(set(data) - LEGACY_KEYS)
        if unknown:
            raise ValueError(f"{LEGACY_BUNDLE}: {locale} non-legacy keys: {', '.join(unknown)}")
        missing = sorted(LEGACY_KEYS - set(data))
        if missing:
            raise ValueError(f"{LEGACY_BUNDLE}: {locale} missing legacy keys: {', '.join(missing)}")
        for key, value in data.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{LEGACY_BUNDLE}: {locale}/{key} invalid translation")
        entries += len(data)
    return len(bundle["translations"]), entries

def validate_sources():
    data = load_json_unique(LEGACY_SOURCES)
    aliases = data.get("aliases", {})
    uncovered = data.get("untranslated_low_confidence", [])
    if not isinstance(aliases, dict) or not isinstance(uncovered, list):
        raise ValueError(f"{LEGACY_SOURCES}: invalid structure")
    for locale, info in aliases.items():
        if not LOCALE_RE.fullmatch(locale) or not isinstance(info, dict):
            raise ValueError(f"{LEGACY_SOURCES}: invalid alias {locale}")
        source = info.get("source")
        if not isinstance(source, str) or not LOCALE_RE.fullmatch(source) or source == locale:
            raise ValueError(f"{LEGACY_SOURCES}: invalid source for {locale}")
    if len(uncovered) != len(set(uncovered)):
        raise ValueError(f"{LEGACY_SOURCES}: duplicate pending locale")
    return len(aliases), len(uncovered)

def main() -> int:
    validate_policy()
    locales, entries = validate_legacy_bundle()
    aliases, pending = validate_sources()
    print(f"Validation OK: {locales} canonical legacy locales, {entries} entries, {aliases} aliases/no-op variants, {pending} low-confidence locales pending")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
