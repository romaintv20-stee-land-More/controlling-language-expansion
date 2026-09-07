#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

CONTROLLING_URL = "https://github.com/jaredlll08/Controlling.git"
MINECRAFT_ASSETS_URL = "https://github.com/InventivetalentDev/minecraft-assets.git"
OUTPUT = Path("data/generated/legacy_pack_audit.json")

TARGETS = [
    {"minecraft": "1.7.10", "controlling_branch": "1.7.10"},
    {"minecraft": "1.8.9", "controlling_branch": "1.8.9"},
    {"minecraft": "1.10.2", "controlling_branch": "1.10.2"},
    {"minecraft": "1.11.2", "controlling_branch": "1.11"},
    {"minecraft": "1.12.2", "controlling_branch": "1.12"},
]

ENGLISH_CANDIDATES = (
    "src/main/resources/assets/controlling/lang/en_US.lang",
    "src/main/resources/assets/controlling/lang/en_us.lang",
)


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def parse_lang(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid .lang line: {raw!r}")
        key, value = line.split("=", 1)
        if key in out:
            raise ValueError(f"Duplicate key: {key}")
        out[key] = value
    return out


def show(repo: Path, ref: str, path: str) -> str | None:
    result = git(repo, "show", f"origin/{ref}:{path}", check=False)
    return result.stdout if result.returncode == 0 else None


def controlling_language_dir(repo: Path, branch: str) -> tuple[str, dict[str, str]]:
    for path in ENGLISH_CANDIDATES:
        text = show(repo, branch, path)
        if text is not None:
            return str(Path(path).parent).replace("\\", "/"), parse_lang(text)
    raise RuntimeError(f"No English .lang found for Controlling {branch}")


def list_controlling_locales(repo: Path, branch: str, lang_dir: str, english: dict[str, str]) -> dict[str, dict]:
    tree = git(repo, "ls-tree", "-r", "--name-only", f"origin/{branch}", "--", lang_dir).stdout
    locales: dict[str, dict] = {}
    for full_path in tree.splitlines():
        if not full_path.endswith(".lang"):
            continue
        name = Path(full_path).name
        if name.lower() == "en_us.lang":
            continue
        text = show(repo, branch, full_path)
        if text is None:
            continue
        data = parse_lang(text)
        locales[Path(name).stem] = {
            "key_count": len(data),
            "missing_keys": sorted(set(english) - set(data)),
            "stale_keys": sorted(set(data) - set(english)),
        }
    return locales


def list_minecraft_locales(repo: Path, version: str) -> list[str]:
    lang_dir = "assets/minecraft/lang"
    tree = git(repo, "ls-tree", "-r", "--name-only", f"origin/{version}", "--", lang_dir).stdout
    locales = []
    for full_path in tree.splitlines():
        name = Path(full_path).name
        if name.endswith(".lang"):
            locales.append(Path(name).stem)
    return sorted(set(locales), key=str.casefold)


def clone_all(url: str, destination: Path) -> None:
    subprocess.run(
        ["git", "clone", "--quiet", "--filter=blob:none", "--no-checkout", url, str(destination)],
        check=True,
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="cle-legacy-audit-") as tmp:
        root = Path(tmp)
        controlling = root / "Controlling"
        mc_assets = root / "minecraft-assets"
        clone_all(CONTROLLING_URL, controlling)
        clone_all(MINECRAFT_ASSETS_URL, mc_assets)

        targets = []
        all_minecraft_locales: set[str] = set()
        for target in TARGETS:
            mc = target["minecraft"]
            branch = target["controlling_branch"]
            lang_dir, english = controlling_language_dir(controlling, branch)
            official = list_controlling_locales(controlling, branch, lang_dir, english)
            minecraft_locales = list_minecraft_locales(mc_assets, mc)
            all_minecraft_locales.update(locale.lower() for locale in minecraft_locales)
            targets.append(
                {
                    **target,
                    "format": "lang",
                    "english_key_count": len(english),
                    "english_keys": list(english),
                    "minecraft_locale_count": len(minecraft_locales),
                    "minecraft_locales": minecraft_locales,
                    "official_controlling_locale_count": len(official),
                    "official_controlling_locales": official,
                }
            )

    report = {
        "pack": "legacy_01",
        "direction": "oldest_to_newest",
        "targets": targets,
        "union_minecraft_locale_count": len(all_minecraft_locales),
        "union_minecraft_locales": sorted(all_minecraft_locales),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Legacy pack audit complete: {len(targets)} Minecraft targets, {len(all_minecraft_locales)} unique locale IDs.")
    for item in targets:
        print(
            f"  {item['minecraft']}: {item['english_key_count']} keys, "
            f"{item['minecraft_locale_count']} Minecraft locales, "
            f"{item['official_controlling_locale_count']} Controlling locale files"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
