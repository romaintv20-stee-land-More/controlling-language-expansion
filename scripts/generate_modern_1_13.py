#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "translations" / "legacy_01.json"
SOURCES = ROOT / "data" / "legacy_locale_sources.json"
OUTPUT = ROOT / "build" / "modern" / "1.13.2"
AUDIT_OUTPUT = ROOT / "data" / "generated" / "modern_1_13_audit.json"

CONTROLLING_URL = "https://github.com/jaredlll08/Controlling.git"
MINECRAFT_ASSETS_URL = "https://github.com/InventivetalentDev/minecraft-assets.git"
TARGET_BRANCH = "1.13"
TARGET_MC = "1.13.2"
DONOR_BRANCH = "1.12"
TARGET_LANG_DIR = "src/main/resources/assets/controlling/lang"
TARGET_ENGLISH = f"{TARGET_LANG_DIR}/en_US.json"
DONOR_LANG_DIR = "src/main/resources/assets/controlling/lang"
DONOR_ENGLISH = f"{DONOR_LANG_DIR}/en_US.lang"
VERSION = "0.1.0-beta-test1"
MOD_ID = "controllinglanguageexpansion"


def run(*args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run("git", "-C", str(repo), *args, check=check)


def clone_all(url: str, destination: Path) -> None:
    run("git", "clone", "--quiet", "--filter=blob:none", "--no-checkout", url, str(destination))


def parse_json_text(text: str) -> dict[str, str]:
    data = json.loads(text)
    if not isinstance(data, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
        raise ValueError("Invalid language JSON")
    return data


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


def show(repo: Path, branch: str, path: str) -> str | None:
    result = git(repo, "show", f"origin/{branch}:{path}", check=False)
    return result.stdout if result.returncode == 0 else None


def branch_json_locales(repo: Path, branch: str, lang_dir: str) -> dict[str, dict[str, str]]:
    tree = git(repo, "ls-tree", "-r", "--name-only", f"origin/{branch}", "--", lang_dir).stdout
    out: dict[str, dict[str, str]] = {}
    for full_path in tree.splitlines():
        if not full_path.lower().endswith(".json"):
            continue
        text = show(repo, branch, full_path)
        if text is not None:
            out[Path(full_path).stem.lower()] = parse_json_text(text)
    return out


def branch_lang_locales(repo: Path, branch: str, lang_dir: str) -> dict[str, dict[str, str]]:
    tree = git(repo, "ls-tree", "-r", "--name-only", f"origin/{branch}", "--", lang_dir).stdout
    out: dict[str, dict[str, str]] = {}
    for full_path in tree.splitlines():
        if not full_path.lower().endswith(".lang"):
            continue
        text = show(repo, branch, full_path)
        if text is not None:
            out[Path(full_path).stem.lower()] = parse_lang(text)
    return out


def minecraft_locales(repo: Path) -> list[str]:
    lang_dir = repo / "assets" / "minecraft" / "lang"
    return sorted({path.stem.lower() for path in lang_dir.glob("*.json")})


def locale_source(
    locale: str,
    key: str,
    target_english: dict[str, str],
    donor_english: dict[str, str],
    donor_locales: dict[str, dict[str, str]],
    canonical: dict[str, dict[str, str]],
    aliases: dict[str, dict[str, str]],
) -> tuple[str | None, str]:
    if donor_english.get(key) == target_english[key]:
        donor = donor_locales.get(locale)
        if donor and key in donor:
            return donor[key], "official_1.12_donor"

    direct = canonical.get(locale)
    if direct and key in direct:
        return direct[key], "canonical_legacy"

    alias = aliases.get(locale)
    if alias:
        source_locale = alias["source"].lower()
        if source_locale == "en_us":
            return target_english[key], alias["status"]
        if donor_english.get(key) == target_english[key]:
            donor = donor_locales.get(source_locale)
            if donor and key in donor:
                return donor[key], alias["status"]
        source_data = canonical.get(source_locale)
        if source_data and key in source_data:
            return source_data[key], alias["status"]

    return None, "missing"


def write_json(path: Path, entries: dict[str, str], key_order: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = {key: entries[key] for key in key_order if key in entries}
    path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def compile_mod_class(work: Path) -> Path:
    src = work / "src"
    classes = work / "classes"
    mod_annotation = src / "net" / "minecraftforge" / "fml" / "common" / "Mod.java"
    mod_class = src / "com" / "steelandmore" / "controllinglanguageexpansion" / "ControllingLanguageExpansion.java"
    mod_annotation.parent.mkdir(parents=True, exist_ok=True)
    mod_class.parent.mkdir(parents=True, exist_ok=True)
    mod_annotation.write_text(
        "package net.minecraftforge.fml.common;\n"
        "import java.lang.annotation.ElementType;\n"
        "import java.lang.annotation.Retention;\n"
        "import java.lang.annotation.RetentionPolicy;\n"
        "import java.lang.annotation.Target;\n"
        "@Retention(RetentionPolicy.RUNTIME)\n"
        "@Target(ElementType.TYPE)\n"
        "public @interface Mod { String value(); }\n",
        encoding="utf-8",
    )
    mod_class.write_text(
        "package com.steelandmore.controllinglanguageexpansion;\n"
        "import net.minecraftforge.fml.common.Mod;\n"
        f"@Mod(\"{MOD_ID}\")\n"
        "public class ControllingLanguageExpansion {\n"
        "    public ControllingLanguageExpansion() {}\n"
        "}\n",
        encoding="utf-8",
    )
    classes.mkdir(parents=True, exist_ok=True)
    run("javac", "--release", "8", "-d", str(classes), str(mod_annotation), str(mod_class))
    result = classes / "com" / "steelandmore" / "controllinglanguageexpansion" / "ControllingLanguageExpansion.class"
    if not result.exists():
        raise RuntimeError("javac did not produce the mod class")
    return result


def build_jar(payload: Path, destination: Path, work: Path) -> None:
    mod_class = compile_mod_class(work)
    manifest = (
        "Manifest-Version: 1.0\n"
        "Implementation-Title: Controlling Language Expansion\n"
        f"Implementation-Version: {VERSION}\n"
        f"Built-For-Minecraft: {TARGET_MC}\n\n"
    )
    mods_toml = f'''modLoader="javafml"
loaderVersion="[25,)"
issueTrackerURL="https://github.com/romaintv20-stee-land-More/controlling-language-expansion/issues"
displayURL="https://github.com/romaintv20-stee-land-More/controlling-language-expansion"
authors="Steel-and-More"

[[mods]]
modId="{MOD_ID}"
version="{VERSION}"
displayName="Controlling Language Expansion"
description="Unofficial localization expansion for Controlling."

[[dependencies.{MOD_ID}]]
modId="forge"
mandatory=true
versionRange="[25,)"
ordering="NONE"
side="CLIENT"

[[dependencies.{MOD_ID}]]
modId="controlling"
mandatory=true
versionRange="[4.0.0,)"
ordering="AFTER"
side="CLIENT"
'''
    pack_mcmeta = json.dumps(
        {"pack": {"pack_format": 4, "description": f"Controlling Language Expansion test resources for Minecraft {TARGET_MC}"}},
        ensure_ascii=False,
        indent=2,
    ) + "\n"

    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("META-INF/MANIFEST.MF", manifest)
        zf.writestr("META-INF/mods.toml", mods_toml)
        zf.writestr(
            "com/steelandmore/controllinglanguageexpansion/ControllingLanguageExpansion.class",
            mod_class.read_bytes(),
        )
        zf.writestr("pack.mcmeta", pack_mcmeta)
        for path in sorted(payload.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(payload).as_posix())


def main() -> int:
    bundle = json.loads(CANONICAL.read_text(encoding="utf-8"))
    canonical = {locale.lower(): data for locale, data in bundle["translations"].items()}
    source_data = json.loads(SOURCES.read_text(encoding="utf-8"))
    aliases = {locale.lower(): info for locale, info in source_data["aliases"].items()}
    excluded = {locale.lower() for locale in source_data["intentionally_excluded_special_locales"]}

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    payload = OUTPUT / "payload"
    payload.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="cle-modern-1-13-") as tmp:
        work = Path(tmp)
        controlling = work / "Controlling"
        mc_assets = work / "minecraft-assets"
        clone_all(CONTROLLING_URL, controlling)
        run("git", "clone", "--quiet", "--depth", "1", "--branch", TARGET_MC, MINECRAFT_ASSETS_URL, str(mc_assets))

        target_text = show(controlling, TARGET_BRANCH, TARGET_ENGLISH)
        donor_text = show(controlling, DONOR_BRANCH, DONOR_ENGLISH)
        if target_text is None or donor_text is None:
            raise RuntimeError("Unable to load target or donor English localization")
        target_english = parse_json_text(target_text)
        donor_english = parse_lang(donor_text)
        official_locales = branch_json_locales(controlling, TARGET_BRANCH, TARGET_LANG_DIR)
        donor_locales = branch_lang_locales(controlling, DONOR_BRANCH, DONOR_LANG_DIR)
        mc_locales = minecraft_locales(mc_assets)

        incomplete: list[dict[str, object]] = []
        excluded_present: list[str] = []
        generated_files = 0
        generated_entries = 0
        source_counts: dict[str, int] = {}

        for locale in mc_locales:
            if locale == "en_us":
                continue
            if locale in excluded:
                excluded_present.append(locale)
                continue

            official = official_locales.get(locale, {})
            fallback: dict[str, str] = {}
            missing: list[str] = []
            for key in target_english:
                if key in official:
                    continue
                value, source = locale_source(
                    locale,
                    key,
                    target_english,
                    donor_english,
                    donor_locales,
                    canonical,
                    aliases,
                )
                source_counts[source] = source_counts.get(source, 0) + 1
                if value is None:
                    missing.append(key)
                elif value != target_english[key]:
                    fallback[key] = value

            if missing:
                incomplete.append({"locale": locale, "missing_keys": missing})
            if fallback:
                write_json(payload / "assets" / "controlling" / "lang" / f"{locale}.json", fallback, list(target_english))
                generated_files += 1
                generated_entries += len(fallback)

        audit = {
            "minecraft": TARGET_MC,
            "controlling_branch": TARGET_BRANCH,
            "format": "json",
            "english_key_count": len(target_english),
            "english_keys": list(target_english),
            "minecraft_locale_count": len(mc_locales),
            "official_controlling_locale_count": len(official_locales) - (1 if "en_us" in official_locales else 0),
            "generated_file_count": generated_files,
            "generated_entry_count": generated_entries,
            "incomplete_locale_count": len(incomplete),
            "incomplete_locales": incomplete,
            "intentionally_excluded_present": sorted(excluded_present),
            "source_counts": source_counts,
        }
        AUDIT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_OUTPUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (OUTPUT / "coverage.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        jar = OUTPUT / f"Controlling-Language-Expansion-{VERSION}-mc{TARGET_MC}.jar"
        build_jar(payload, jar, work / "jar-build")

    print(
        f"Minecraft {TARGET_MC}: {len(mc_locales)} locales, {generated_files} fallback files, "
        f"{generated_entries} entries, {len(incomplete)} incomplete locales, "
        f"{len(excluded_present)} intentionally excluded locales present."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
