# Marathi language expansion — 1.0.1 (not yet published)

The Marathi-inclusive 1.0.1 build is a **static-validated release candidate**. It is not automatically published to CurseForge or Modrinth.

## Downloads

The repository's `release-candidates/1.0.1/` directory contains two separate outputs:

- `Controlling-Language-Expansion-1.0.1-mc1.21.9-26.3-marathi.jar` — existing multi-loader 1.0.1 JAR, plus the complete new `mr_in` Controlling locale.
- `Minecraft-26.3-Marathi-mr_in-1.0.1.zip` — the companion **Minecraft 26.3-only** resource pack that registers Marathi (`मराठी`) in the language menu and provides the vanilla UI, item, block and other text.

### Installation

Copy the JAR to your Minecraft instance's `mods/` folder alongside Controlling. Leave the accompanying Minecraft ZIP intact in `resourcepacks/`, enable it in-game, then choose `मराठी` (Marathi) from Language settings. The ZIP is specifically keyed to Minecraft 26.3 and its resource-pack format 97.1; do not advertise the ZIP as compatible with other Minecraft versions without a separate source-key audit.

The Controlling JAR retains the baseline's multi-version range **Minecraft 1.21.9–26.3**, its original Fabric/Forge/NeoForge metadata and all 126 existing language resource files. The additional Marathi file covers all **12 official Controlling keys**.

## Minecraft source and coverage

The Marathi Minecraft pack is derived **directly from the user's Beyond & More 26.1.2** `assets/minecraft/lang/mr_in.json`, SHA-256 `3881d10637b21a890ff40c631937852ee60d60669dce45d25686c1b4d0f079f8`. The actual English source keys were independently retrieved from official Minecraft 26.1.2 and 26.3 client JARs:

| Source | English keys |
|---|---:|
| Minecraft 26.1.2 / Beyond & More | 7,886 |
| Minecraft 26.3 | 8,559 |
| Added keys | 673 |
| Changed English values | 95 |
| Removed keys | 0 |

The 8,559-key pack combines **7,790 exact same-key/same-English Beyond & More values**, **45 verified identical-English cross-key values**, **2 curated fixes** (including correcting `language.code` from `en_us` to `mr_in`), and **722 machine-assisted Marathi translations** for the remaining added/changed keys.

The 722 machine-assisted values require native-speaker proofreading before calling the localization human-verified. The source also intentionally retains **248 English-identical values**, predominantly technical/UI tokens, keyboard key names, identifiers and format-only strings. All 1,082 official placeholder/technical-token signatures passed static checks.

The official Minecraft 26.3 asset index contains no `mr_in` locale. The companion pack declares the new language using Minecraft's `pack.mcmeta` custom `language` section, and embeds `assets/minecraft/lang/mr_in.json`.

## English changelog — CurseForge / Modrinth

Controlling Language Expansion 1.0.1 — Marathi Update

- Added complete Marathi (`mr_in`) coverage for all 12 current Controlling translation keys.
- Preserved all 126 existing Controlling language files and official upstream translation priority.
- Added an optional standalone Minecraft 26.3 Marathi resource pack covering 8,559 vanilla localization keys, adapted from Beyond & More's 26.1.2 Marathi files.
- Matched 673 newly introduced Minecraft keys and re-evaluated 95 changed English source strings.
- Machine-assisted translations were used for 722 new/changed entries; native-language review remains outstanding.
- Verified placeholders, JSON syntax, original loader metadata, and the original JAR entry contents.
- Supports Controlling on Minecraft 1.21.9–26.3; the companion Minecraft resource pack targets Minecraft 26.3 specifically.

The Marathi-inclusive JAR and companion pack have passed static checks, but in-game language-menu, font-rendering and loader compatibility testing remains to be performed before public publication.

## Reproduction and validation

The pinned 1.0.1 base JAR is stored under `vendor/` only to preserve the original compiled loader classes and existing translations. All original ZIP entry contents are compared byte-for-byte with the new candidate, apart from the single added `mr_in.json` entry. Build with `python scripts/build_marathi_1_0_1.py`; check with `python scripts/validate_marathi_1_0_1.py`.

The source derivation generator `scripts/prepare_marathi_26_3.py` can be rerun when the original Beyond & More Marathi JSON and both official English JSONs are available. `scripts/freeze_minecraft_26_3_signatures.py` creates the non-English-content upstream key/placeholder reference used by CI.

**Release gate:** Do not promote a statically validated candidate to a verified final release until Minecraft 26.3 plus Controlling is tested in-game with the language ZIP enabled and Devanagari glyph rendering checked.
