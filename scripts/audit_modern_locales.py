#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

UPSTREAM = "https://github.com/jaredlll08/Controlling.git"
BRANCH = "26.2"
LANG_DIR = "common/src/main/resources/assets/controlling/lang"
ENGLISH = f"{LANG_DIR}/en_us.json"
OUTPUT = Path("data/generated/modern_locale_audit.json")


def run(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(args, cwd=cwd, check=True, text=True, stdout=subprocess.PIPE).stdout


def parse(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
        raise ValueError(f"Invalid language file: {path}")
    return data


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="controlling-modern-") as tmp:
        repo = Path(tmp) / "Controlling"
        run("git", "clone", "--quiet", "--depth", "1", "--branch", BRANCH, UPSTREAM, str(repo))
        english = parse(repo / ENGLISH)
        report: dict[str, object] = {
            "branch": BRANCH,
            "english_key_count": len(english),
            "official_locales": {},
        }
        for path in sorted((repo / LANG_DIR).glob("*.json")):
            if path.name == "en_us.json":
                continue
            data = parse(path)
            missing = sorted(set(english) - set(data))
            stale = sorted(set(data) - set(english))
            report["official_locales"][path.stem] = {
                "key_count": len(data),
                "missing_keys": missing,
                "stale_keys": stale,
                "complete": not missing and not stale,
            }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    complete = sum(1 for x in report["official_locales"].values() if x["complete"])
    print(f"Controlling {BRANCH}: {len(report['official_locales'])} official non-English locales; {complete} complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
