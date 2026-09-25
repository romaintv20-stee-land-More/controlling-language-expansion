# Controlling Language Expansion 1.0.1 — Marathi (single JAR)

**Status:** static-validated candidate, not a published Marathi release. One JAR contains both the Controlling translations and the Minecraft Marathi language resources. There is **no second ZIP to install**.

## Single download and installation

The sole candidate artifact is `release-candidates/1.0.1/Controlling-Language-Expansion-1.0.1-mc1.21.9-26.3-marathi-all-in-one.jar`.

Place this JAR in your Minecraft instance's `mods/` folder alongside the original **Controlling** mod, which remains a required dependency. The JAR contains the custom-language registration in its own `pack.mcmeta` and both namespaced translations:

- `assets/controlling/lang/mr_in.json` — 12 keys for Controlling.
- `assets/minecraft/lang/mr_in.json` — 8,559 vanilla keys for Minecraft 26.3.
- `pack.mcmeta` — adds `mr_in` (`मराठी`, `भारत`) without changing the original compatibility range 69.0–97.1.

The JAR preserves the original compiled Forge/NeoForge/Fabric entrypoints, all 126 existing Controlling locales and all mod metadata. The language should become selectable from Minecraft's language menu when the loader includes this mod's resource pack. **This integration still requires an in-game test** on each claimed loader. No standalone resource-pack ZIP is distributed.

**Version scoping:** Controlling's original JAR declares Minecraft **1.21.9–26.3**. The embedded *Minecraft* Marathi translation was audited specifically for **26.3**; coverage and vocabulary for other Minecraft versions must not be claimed without separate source audits.

## Translation provenance and completeness

The vanilla Marathi source was retrieved **directly from Beyond & More 26.1.2** `assets/minecraft/lang/mr_in.json` (SHA-256 `3881d10637b21a890ff40c631937852ee60d60669dce45d25686c1b4d0f079f8`) and audited against official Minecraft 26.1.2 and 26.3 English resource files.

| Metric | Count |
|---|---:|
| Official Minecraft 26.1.2 keys | 7,886 |
| Official Minecraft 26.3 keys | 8,559 |
| Added 26.3 keys | 673 |
| Changed English meanings | 95 |
| Removed keys | 0 |
| Exact same-key/same-English Beyond & More reuses | 7,790 |
| Verified unique identical-English cross-key reuses | 45 |
| Curated corrections (including `language.code=mr_in`) | 2 |
| Machine-assisted new/changed Marathi entries | 722 |
| Official technical-token signatures tested | 1,082 |

The 722 machine-assisted strings require a native Marathi review. Some 248 entries still match their English source values; most represent identifiers, keyboard names, technical tokens and formatting-only strings. A complete key inventory **does not imply a human-reviewed translation**.

## Changelog — CurseForge / Modrinth

Controlling Language Expansion 1.0.1 — Marathi Update

- Added a complete Marathi (`mr_in`) translation for all 12 Controlling localization keys.
- Added the Minecraft 26.3 Marathi language pack **inside the same JAR**, registering Marathi in the Minecraft language menu. No additional ZIP is required.
- Includes all 8,559 official Minecraft 26.3 translation keys, adapting 7,835 verified Beyond & More translations and adding 722 machine-assisted values for new or changed text.
- Preserves all 126 existing Controlling language files, original loader classes and published dependency metadata.
- Verified JSON coverage, technical placeholders, language metadata, reproducible JAR content and SHA-256.
- The Controlling mod's declared Minecraft range remains 1.21.9–26.3; embedded vanilla Marathi text is audited specifically for Minecraft 26.3.

**Review/testing:** Marathi native-speaker proofreading, in-game language selection, Devanagari font rendering and Forge/NeoForge/Fabric runtime tests remain open. This is not yet a verified public release.

## Build and verification

Run `python scripts/build_marathi_1_0_1.py` and `python scripts/validate_marathi_1_0_1.py`. Both operate on the pinned original 1.0.1 JAR in `vendor/` and the checked-in 12-key Controlling/8,559-key Minecraft source files. The validator requires that **every original archive entry is unchanged except `pack.mcmeta`**, and checks the two additions (`mr_in` for Controlling and Minecraft).

Run `python scripts/prepare_marathi_26_3.py` to re-audit the Beyond & More source when both official Minecraft English sources are available. The frozen 26.3 key and placeholder-signature inventory enables offline CI checks. The canonical candidate lives under `release-candidates/1.0.1/` with its SHA-256 manifest; no separate ZIP is required.
