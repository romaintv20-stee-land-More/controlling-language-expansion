#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PATH = ROOT / "translations" / "legacy_01.json"
EXTRA_PATH = ROOT / "translations" / "modern_extra.json"
LEGACY_SOURCES_PATH = ROOT / "data" / "legacy_locale_sources.json"
MODERN_SOURCES_PATH = ROOT / "data" / "modern_locale_sources.json"
OUTPUT_ROOT = ROOT / "build" / "modern"
AUDIT_OUTPUT = ROOT / "data" / "generated" / "modern_pack_audit.json"

CONTROLLING_URL = "https://github.com/jaredlll08/Controlling.git"
MINECRAFT_ASSETS_API = "https://api.github.com/repos/InventivetalentDev/minecraft-assets/contents/assets/minecraft/lang"

TARGET_BRANCHES = [
    "1.13", "1.14.2", "1.15", "1.16", "1.17", "1.18", "1.19",
    "1.19.3", "1.19.4", "1.20", "1.20.1", "1.20.2", "1.20.3", "1.20.4",
    "1.20.5", "1.20.6", "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4",
    "1.21.5", "1.21.6", "1.21.7", "1.21.8", "1.21.9", "1.21.10", "1.21.11",
    "26.1", "26.1.1", "26.1.2", "26.2",
]

MC_ASSET_REF_OVERRIDES = {
    "1.13": "1.13.2",
}

VERSION = "1.0.0-test1"
MOD_ID = "controllinglanguageexpansion"
ALL_KEYS = [
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
    "options.sortKeyAZ",
    "options.sortKeyZA",
    "options.toggleFree",
    "options.confirmReset",
]


@dataclass
class BranchInfo:
    branch: str
    english_path: str
    lang_dir: str
    english: dict[str, str]
    locale_paths: dict[str, str]


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run("git", "-C", str(repo), *args, check=check)


def show(repo: Path, branch: str, path: str) -> str | None:
    result = git(repo, "show", f"origin/{branch}:{path}", check=False)
    return result.stdout if result.returncode == 0 else None


def parse_json_text(text: str) -> dict[str, str]:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Language JSON is not an object")
    return {str(k): str(v) for k, v in data.items() if isinstance(k, str) and isinstance(v, str)}


def find_branch_info(repo: Path, branch: str) -> BranchInfo:
    tree = git(repo, "ls-tree", "-r", "--name-only", f"origin/{branch}").stdout.splitlines()
    lang_json = [path for path in tree if "/lang/" in path and path.lower().endswith(".json")]
    english_candidates = [
        path for path in lang_json
        if Path(path).name.lower() == "en_us.json" and "assets/controlling/lang/" in path.lower()
    ]
    if not english_candidates:
        raise RuntimeError(f"{branch}: no Controlling en_us.json found")
    english_path = min(english_candidates, key=len)
    lang_dir = str(Path(english_path).parent).replace("\\", "/")
    english_text = show(repo, branch, english_path)
    if english_text is None:
        raise RuntimeError(f"{branch}: cannot read {english_path}")
    english = parse_json_text(english_text)
    locale_paths: dict[str, str] = {}
    prefix = lang_dir.lower() + "/"
    for path in lang_json:
        if path.lower().startswith(prefix):
            locale_paths[Path(path).stem.lower()] = path
    return BranchInfo(branch, english_path, lang_dir, english, locale_paths)


def minecraft_locales(ref: str) -> list[str]:
    url = MINECRAFT_ASSETS_API + "?ref=" + urllib.parse.quote(ref, safe="")
    req = urllib.request.Request(url, headers={"User-Agent": "controlling-language-expansion-audit"})
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            items = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Minecraft asset locale listing failed for {ref}: HTTP {exc.code}") from exc
    locales = {
        Path(item["name"]).stem.lower()
        for item in items
        if item.get("type") == "file" and str(item.get("name", "")).lower().endswith(".json")
    }
    return sorted(locales)


def merge_aliases() -> tuple[dict[str, dict[str, str]], set[str], set[str]]:
    legacy = json.loads(LEGACY_SOURCES_PATH.read_text(encoding="utf-8"))
    modern = json.loads(MODERN_SOURCES_PATH.read_text(encoding="utf-8"))
    aliases: dict[str, dict[str, str]] = {}
    aliases.update({k.lower(): v for k, v in legacy.get("aliases", {}).items()})
    aliases.update({k.lower(): v for k, v in modern.get("aliases", {}).items()})
    excluded = {x.lower() for x in legacy.get("intentionally_excluded_special_locales", [])}
    deferred = {x.lower() for x in modern.get("deferred_low_coverage_real_locales", {})}
    return aliases, excluded, deferred


def load_memory() -> dict[str, dict[str, str]]:
    canonical_raw = json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))["translations"]
    extra_raw = json.loads(EXTRA_PATH.read_text(encoding="utf-8"))["translations"]
    memory = {locale.lower(): dict(values) for locale, values in canonical_raw.items()}
    for locale, values in extra_raw.items():
        memory.setdefault(locale.lower(), {}).update(values)
    return memory


def write_json(path: Path, entries: dict[str, str], key_order: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = {key: entries[key] for key in key_order if key in entries}
    path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def compile_mod_classes(work: Path) -> list[tuple[str, bytes]]:
    src = work / "src"
    classes = work / "classes"
    forge_annotation = src / "net" / "minecraftforge" / "fml" / "common" / "Mod.java"
    neo_annotation = src / "net" / "neoforged" / "fml" / "common" / "Mod.java"
    forge_class = src / "com" / "steelandmore" / "controllinglanguageexpansion" / "ForgeEntrypoint.java"
    neo_class = src / "com" / "steelandmore" / "controllinglanguageexpansion" / "NeoForgeEntrypoint.java"
    for path in (forge_annotation, neo_annotation, forge_class, neo_class):
        path.parent.mkdir(parents=True, exist_ok=True)
    annotation_source = (
        "import java.lang.annotation.ElementType;\n"
        "import java.lang.annotation.Retention;\n"
        "import java.lang.annotation.RetentionPolicy;\n"
        "import java.lang.annotation.Target;\n"
        "@Retention(RetentionPolicy.RUNTIME)\n"
        "@Target(ElementType.TYPE)\n"
        "public @interface Mod { String value(); }\n"
    )
    forge_annotation.write_text("package net.minecraftforge.fml.common;\n" + annotation_source, encoding="utf-8")
    neo_annotation.write_text("package net.neoforged.fml.common;\n" + annotation_source, encoding="utf-8")
    forge_class.write_text(
        "package com.steelandmore.controllinglanguageexpansion;\n"
        "import net.minecraftforge.fml.common.Mod;\n"
        f"@Mod(\"{MOD_ID}\")\n"
        "public final class ForgeEntrypoint { public ForgeEntrypoint() {} }\n",
        encoding="utf-8",
    )
    neo_class.write_text(
        "package com.steelandmore.controllinglanguageexpansion;\n"
        "import net.neoforged.fml.common.Mod;\n"
        f"@Mod(\"{MOD_ID}\")\n"
        "public final class NeoForgeEntrypoint { public NeoForgeEntrypoint() {} }\n",
        encoding="utf-8",
    )
    classes.mkdir(parents=True, exist_ok=True)
    run(
        "javac", "--release", "8", "-d", str(classes),
        str(forge_annotation), str(neo_annotation), str(forge_class), str(neo_class),
    )
    out: list[tuple[str, bytes]] = []
    for name in ("ForgeEntrypoint", "NeoForgeEntrypoint"):
        path = classes / "com" / "steelandmore" / "controllinglanguageexpansion" / f"{name}.class"
        out.append((f"com/steelandmore/controllinglanguageexpansion/{name}.class", path.read_bytes()))
    return out


def pack_format_for(version: str) -> int:
    if version.startswith("1.13") or version.startswith("1.14"):
        return 4
    if version.startswith("1.15"):
        return 5
    if version.startswith("1.16"):
        return 6
    if version.startswith("1.17"):
        return 7
    if version.startswith("1.18"):
        return 8
    if version in {"1.19", "1.19.1", "1.19.2"}:
        return 9
    if version == "1.19.3":
        return 12
    if version == "1.19.4":
        return 13
    if version in {"1.20", "1.20.1"}:
        return 15
    if version == "1.20.2":
        return 18
    if version in {"1.20.3", "1.20.4"}:
        return 22
    if version in {"1.20.5", "1.20.6"}:
        return 32
    if version.startswith("1.21") or version.startswith("26."):
        return 34
    return 15


def build_jar(payload: Path, destination: Path, minecraft_version: str, classes: list[tuple[str, bytes]]) -> None:
    manifest = (
        "Manifest-Version: 1.0\n"
        "Implementation-Title: Controlling Language Expansion\n"
        f"Implementation-Version: {VERSION}\n"
        f"Built-For-Minecraft: {minecraft_version}\n\n"
    )
    mods_toml = f'''modLoader="javafml"
loaderVersion="[25,)"
license="MIT"
issueTrackerURL="https://github.com/romaintv20-stee-land-More/controlling-language-expansion/issues"
displayURL="https://github.com/romaintv20-stee-land-More/controlling-language-expansion"
authors="Steel-and-More"

[[mods]]
modId="{MOD_ID}"
version="{VERSION}"
displayName="Controlling Language Expansion"
description="Unofficial localization expansion for Controlling."

[[dependencies.{MOD_ID}]]
modId="controlling"
mandatory=true
versionRange="[4.0.0,)"
ordering="AFTER"
side="CLIENT"
'''
    neoforge_toml = f'''modLoader="javafml"
loaderVersion="[1,)"
license="MIT"

[[mods]]
modId="{MOD_ID}"
version="{VERSION}"
displayName="Controlling Language Expansion"
authors="Steel-and-More"
description="Unofficial localization expansion for Controlling."
'''
    fabric_json = {
        "schemaVersion": 1,
        "id": MOD_ID,
        "version": VERSION,
        "name": "Controlling Language Expansion",
        "description": "Unofficial localization expansion for Controlling.",
        "authors": ["Steel-and-More"],
        "environment": "client",
        "depends": {"minecraft": "*"},
        "suggests": {"controlling": "*"},
    }
    pack_mcmeta = {
        "pack": {
            "pack_format": pack_format_for(minecraft_version),
            "description": f"Controlling Language Expansion for Minecraft {minecraft_version}",
        }
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("META-INF/MANIFEST.MF", manifest)
        zf.writestr("META-INF/mods.toml", mods_toml)
        zf.writestr("META-INF/neoforge.mods.toml", neoforge_toml)
        zf.writestr("fabric.mod.json", json.dumps(fabric_json, ensure_ascii=False, indent=2) + "\n")
        zf.writestr("pack.mcmeta", json.dumps(pack_mcmeta, ensure_ascii=False, indent=2) + "\n")
        for arcname, content in classes:
            zf.writestr(arcname, content)
        for path in sorted(payload.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(payload).as_posix())


def main() -> int:
    memory = load_memory()
    aliases, excluded_special, deferred_low_coverage = merge_aliases()

    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="cle-modern-all-") as tmp:
        work = Path(tmp)
        controlling = work / "Controlling"
        run("git", "clone", "--quiet", "--no-checkout", CONTROLLING_URL, str(controlling))
        branch_infos = {branch: find_branch_info(controlling, branch) for branch in TARGET_BRANCHES}

        official_cache: dict[tuple[str, str], dict[str, str]] = {}

        def official(branch: str, locale: str) -> dict[str, str]:
            cache_key = (branch, locale)
            if cache_key in official_cache:
                return official_cache[cache_key]
            info = branch_infos[branch]
            path = info.locale_paths.get(locale)
            if not path:
                official_cache[cache_key] = {}
                return {}
            text = show(controlling, branch, path)
            data = parse_json_text(text) if text is not None else {}
            official_cache[cache_key] = data
            return data

        donor_order = list(reversed(TARGET_BRANCHES))
        resolving: set[tuple[str, str, str]] = set()

        def resolve(branch: str, locale: str, key: str) -> tuple[str | None, str]:
            marker = (branch, locale, key)
            if marker in resolving:
                return None, "cycle"
            resolving.add(marker)
            try:
                target_english = branch_infos[branch].english.get(key)

                # Official translation from any audited Controlling branch wins when the English meaning is identical.
                if target_english is not None:
                    for donor_branch in donor_order:
                        donor_info = branch_infos[donor_branch]
                        if donor_info.english.get(key) != target_english:
                            continue
                        donor_value = official(donor_branch, locale).get(key)
                        if donor_value:
                            source = "official_target" if donor_branch == branch else f"official_donor:{donor_branch}"
                            return donor_value, source

                direct = memory.get(locale, {}).get(key)
                if direct:
                    return direct, "translation_memory"

                alias = aliases.get(locale)
                if alias:
                    source_locale = str(alias["source"]).lower()
                    value, _ = resolve(branch, source_locale, key)
                    if value:
                        return value, str(alias.get("status", "alias"))

                if key in {"options.sortKeyAZ", "options.sortKeyZA"}:
                    key_value, _ = resolve(branch, locale, "options.key")
                    if key_value:
                        suffix = "A->Z" if key.endswith("AZ") else "Z->A"
                        return f"{key_value} {suffix}", "derived_sort_key"

                return None, "missing"
            finally:
                resolving.discard(marker)

        classes = compile_mod_classes(work / "classes-build")
        audits: dict[str, object] = {}
        total_jars = 0
        total_incomplete = 0

        for branch in TARGET_BRANCHES:
            info = branch_infos[branch]
            mc_ref = MC_ASSET_REF_OVERRIDES.get(branch, branch)
            locales = minecraft_locales(mc_ref)
            target_dir = OUTPUT_ROOT / mc_ref
            payload = target_dir / "payload"
            payload.mkdir(parents=True, exist_ok=True)
            incomplete: list[dict[str, object]] = []
            deferred_present: list[str] = []
            excluded_present: list[str] = []
            generated_files = 0
            generated_entries = 0
            source_counts: dict[str, int] = {}

            for locale in locales:
                if locale == "en_us":
                    continue
                if locale in excluded_special:
                    excluded_present.append(locale)
                    continue
                if locale in deferred_low_coverage:
                    deferred_present.append(locale)
                    continue

                target_official = official(branch, locale)
                fallback: dict[str, str] = {}
                missing: list[str] = []
                for key, english_value in info.english.items():
                    if key in target_official:
                        continue
                    value, source = resolve(branch, locale, key)
                    source_counts[source] = source_counts.get(source, 0) + 1
                    if value is None:
                        missing.append(key)
                    elif value != english_value:
                        fallback[key] = value

                if missing:
                    incomplete.append({"locale": locale, "missing_keys": missing})
                if fallback:
                    write_json(payload / "assets" / "controlling" / "lang" / f"{locale}.json", fallback, list(info.english))
                    generated_files += 1
                    generated_entries += len(fallback)

            jar = target_dir / f"Controlling-Language-Expansion-{VERSION}-mc{mc_ref}.jar"
            build_jar(payload, jar, mc_ref, classes)
            total_jars += 1
            total_incomplete += len(incomplete)
            branch_audit = {
                "controlling_branch": branch,
                "minecraft": mc_ref,
                "english_key_count": len(info.english),
                "minecraft_locale_count": len(locales),
                "official_controlling_locale_count": max(0, len(info.locale_paths) - 1),
                "generated_file_count": generated_files,
                "generated_entry_count": generated_entries,
                "incomplete_locale_count": len(incomplete),
                "incomplete_locales": incomplete,
                "deferred_low_coverage_real_locales_present": sorted(deferred_present),
                "intentionally_excluded_special_locales_present": sorted(excluded_present),
                "source_counts": source_counts,
                "jar": str(jar.relative_to(ROOT)),
            }
            (target_dir / "coverage.json").write_text(json.dumps(branch_audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            audits[branch] = branch_audit
            print(
                f"{branch} -> {mc_ref}: {len(locales)} locales, {generated_files} fallback files, "
                f"{len(incomplete)} incomplete, {len(deferred_present)} deferred, {len(excluded_present)} excluded"
            )

        summary = {
            "version": VERSION,
            "target_count": len(TARGET_BRANCHES),
            "jar_count": total_jars,
            "total_incomplete_locale_targets": total_incomplete,
            "targets": audits,
        }
        AUDIT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (OUTPUT_ROOT / "coverage.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if total_incomplete:
        print(f"WARNING: {total_incomplete} incomplete locale/target combinations remain.")
    else:
        print(f"All {total_jars} modern test jars generated with no non-deferred missing translations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
