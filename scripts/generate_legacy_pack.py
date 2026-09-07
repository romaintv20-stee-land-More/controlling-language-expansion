#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data" / "generated" / "legacy_pack_audit.json"
BUNDLE = ROOT / "translations" / "legacy_01.json"
SOURCES = ROOT / "data" / "legacy_locale_sources.json"
OUTPUT = ROOT / "build" / "legacy"
CONTROLLING_URL = "https://github.com/jaredlll08/Controlling.git"

ENGLISH_CANDIDATES = (
    "src/main/resources/assets/controlling/lang/en_US.lang",
    "src/main/resources/assets/controlling/lang/en_us.lang",
)

def git(repo: Path, *args: str, check: bool = True):
    return subprocess.run(["git", "-C", str(repo), *args], check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def parse_lang(text: str) -> dict[str, str]:
    out = {}
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

def show(repo: Path, branch: str, path: str):
    result = git(repo, "show", f"origin/{branch}:{path}", check=False)
    return result.stdout if result.returncode == 0 else None

def language_dir_and_english(repo: Path, branch: str):
    for path in ENGLISH_CANDIDATES:
        text = show(repo, branch, path)
        if text is not None:
            return str(Path(path).parent).replace("\\", "/"), parse_lang(text)
    raise RuntimeError(f"No English localization for Controlling branch {branch}")

def branch_locales(repo: Path, branch: str, lang_dir: str):
    tree = git(repo, "ls-tree", "-r", "--name-only", f"origin/{branch}", "--", lang_dir).stdout
    result = {}
    for full_path in tree.splitlines():
        if not full_path.endswith(".lang"):
            continue
        text = show(repo, branch, full_path)
        if text is not None:
            result[Path(full_path).stem.lower()] = parse_lang(text)
    return result

def load_canonical():
    data = json.loads(BUNDLE.read_text(encoding="utf-8"))
    return {k.lower(): v for k, v in data["translations"].items()}

def locale_source(locale, key, target_english, donor_english, donor_locales, canonical, aliases):
    if donor_english.get(key) == target_english[key]:
        donor = donor_locales.get(locale)
        if donor and key in donor:
            return donor[key], "official_1.12_donor"
    direct = canonical.get(locale)
    if direct and key in direct:
        return direct[key], "canonical"
    alias = aliases.get(locale)
    if alias:
        source = alias["source"].lower()
        if source == "en_us":
            return target_english[key], alias["status"]
        if donor_english.get(key) == target_english[key]:
            donor = donor_locales.get(source)
            if donor and key in donor:
                return donor[key], alias["status"]
        source_data = canonical.get(source)
        if source_data and key in source_data:
            return source_data[key], alias["status"]
    return None, "missing"

def write_lang(path: Path, entries: dict[str, str], key_order: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"{key}={entries[key]}" for key in key_order if key in entries) + "\n", encoding="utf-8")

def zip_directory(source: Path, destination: Path):
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(source))

def main() -> int:
    if not AUDIT.exists():
        raise SystemExit("Run scripts/audit_legacy_pack.py first.")
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    source_data = json.loads(SOURCES.read_text(encoding="utf-8"))
    aliases = {k.lower(): v for k, v in source_data["aliases"].items()}
    canonical = load_canonical()
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)

    with tempfile.TemporaryDirectory(prefix="cle-generate-legacy-") as tmp:
        repo = Path(tmp) / "Controlling"
        subprocess.run(["git", "clone", "--quiet", "--filter=blob:none", "--no-checkout", CONTROLLING_URL, str(repo)], check=True)
        donor_dir, donor_english = language_dir_and_english(repo, "1.12")
        donor_locales = branch_locales(repo, "1.12", donor_dir)
        reports = []
        for target in audit["targets"]:
            mc = target["minecraft"]
            branch = target["controlling_branch"]
            lang_dir, english = language_dir_and_english(repo, branch)
            target_locales = branch_locales(repo, branch, lang_dir)
            root = OUTPUT / mc
            payload = root / "payload"
            incomplete = []
            generated_files = generated_entries = 0
            source_counts = {}
            for original_locale in target["minecraft_locales"]:
                locale = original_locale.lower()
                if locale == "en_us":
                    continue
                official = target_locales.get(locale, {})
                fallback = {}
                missing = []
                for key in english:
                    if key in official:
                        continue
                    value, source = locale_source(locale, key, english, donor_english, donor_locales, canonical, aliases)
                    source_counts[source] = source_counts.get(source, 0) + 1
                    if value is None:
                        missing.append(key)
                    elif value != english[key]:
                        fallback[key] = value
                if missing:
                    incomplete.append({"locale": locale, "missing_keys": missing})
                if fallback:
                    write_lang(payload / "assets" / "controlling" / "lang" / f"{original_locale}.lang", fallback, list(english))
                    generated_files += 1
                    generated_entries += len(fallback)
            if payload.exists():
                zip_directory(payload, root / f"controlling-language-expansion-{mc}-payload.zip")
            reports.append({
                "minecraft": mc,
                "controlling_branch": branch,
                "english_key_count": len(english),
                "minecraft_locale_count": target["minecraft_locale_count"],
                "generated_file_count": generated_files,
                "generated_entry_count": generated_entries,
                "incomplete_locale_count": len(incomplete),
                "incomplete_locales": incomplete,
                "source_counts": source_counts,
            })
    report = {"pack": "legacy_01", "canonical_locale_count": len(canonical), "targets": reports}
    (OUTPUT / "coverage.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total_incomplete = sum(t["incomplete_locale_count"] for t in reports)
    print(f"Generated legacy pack from {len(canonical)} canonical locales; {total_incomplete} incomplete target-locale combinations remain.")
    for target in reports:
        print(f"  {target['minecraft']}: {target['generated_file_count']} fallback files, {target['generated_entry_count']} entries, {target['incomplete_locale_count']} incomplete locales")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
