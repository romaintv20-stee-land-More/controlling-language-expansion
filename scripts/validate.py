#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANSLATIONS = ROOT / "translations"
POLICY = ROOT / "data" / "project_policy.json"


def load_json_unique(path: Path):
    def hook(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError(f"{path}: duplicate key {key!r}")
            out[key] = value
        return out

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=hook)


def validate_policy() -> None:
    data = load_json_unique(POLICY)
    required = {
        "project_version",
        "minecraft_min",
        "minecraft_max",
        "locale_policy",
        "official_upstream_priority",
        "upstream_repository",
        "release_status",
    }
    missing = sorted(required - set(data))
    if missing:
        raise ValueError(f"{POLICY}: missing fields: {', '.join(missing)}")
    if data["official_upstream_priority"] is not True:
        raise ValueError("Official upstream priority must remain enabled")


def validate_translations() -> tuple[int, int]:
    locale_count = 0
    entry_count = 0
    for path in sorted(TRANSLATIONS.glob("*.json")):
        data = load_json_unique(path)
        if not isinstance(data, dict):
            raise ValueError(f"{path}: expected JSON object")
        for key, value in data.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError(f"{path}: translation keys and values must be strings")
            if not key.strip():
                raise ValueError(f"{path}: empty translation key")
        locale_count += 1
        entry_count += len(data)
    return locale_count, entry_count


def main() -> int:
    validate_policy()
    locales, entries = validate_translations()
    print(f"Validation OK: {locales} canonical locale files, {entries} translation entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
