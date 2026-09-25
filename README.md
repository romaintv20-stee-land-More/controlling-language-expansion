# Controlling Language Expansion

Unofficial localization companion for [Controlling](https://github.com/jaredlll08/Controlling), focused on broad language coverage and historical Minecraft compatibility.

## Goals

- Cover Controlling from Minecraft 1.7.10 through current releases where technically feasible.
- Support nearly every real language available in Minecraft Java Edition for each supported Minecraft generation.
- Preserve official Controlling translations as the first priority.
- Provide only missing localization keys whenever an official translation already exists.
- Reuse translations across Minecraft versions when the upstream English keys and meanings are identical.
- Support both legacy `.lang` files and modern `.json` language files.
- Audit upstream changes automatically so obsolete fallbacks can be removed when Controlling gains official translations.

## Project status

The add-on has **17 published CurseForge files** through Minecraft 26.3. The latest multi-version release is **Controlling Language Expansion 1.0.1**, uploaded September 17, 2026, covering Minecraft **1.21.9 through 26.3**. It contains 126 JSON localization files and preserves all translations supplied by Controlling.

- [Current CurseForge release (file 8901886)](https://www.curseforge.com/minecraft/mc-mods/controlling-language-expansion/files/8901886)
- [Upstream Controlling](https://www.curseforge.com/minecraft/mc-mods/controlling)

### September 25, 2026 upstream compatibility audit

Controlling released **26.3.3** for Fabric and NeoForge on September 19. Comparing the Minecraft 26.3 initial port `2db798a` with the latest branch commit `d7426fa` confirms that the intervening changes concern Fabric's mod ID in event handlers, **not localization**: all 24 upstream language JSON files, including the 12-key English source, are byte-identical.

The published 1.0.1 JAR was checked directly: 126 locale files; correct namespace; no overlap with official Controlling translations; Forge, NeoForge and Fabric metadata; and a resource-pack compatibility range of 69.0–97.1, including Minecraft 26.3. **No translation-only JAR rebuild is required for Controlling 26.3.3.** Actual in-game testing remains separate from these static checks. See [the frozen audit](data/upstream_release_26_3_audit.json).

This source repository contains the historic auditing, validation and early-generation translation tools. It does not yet contain a complete reproducible build workflow for every existing CurseForge release.

### Audited upstream localization generations

The automated upstream audit now covers 38 numbered branches from 1.7.10 through 26.3. Seven distinct English localization generations and 15 unique English keys appear across the audited history:

- Generation 01 — `.lang`, 13 keys: 1.7.10, 1.8.9, 1.10.2, 1.12
- Generation 02 — `.lang`, 9 keys: 1.11
- Generation 03 — `.json`, 9 keys: 1.13
- Generation 04 — `.json`, 13 keys: 1.14.2 through 1.19
- Generation 05 — `.json`, 12 keys: 1.19.3 through 1.20.4
- Generation 06 — `.json`, 14 keys: 1.20.5, 1.20.6, 1.21
- Generation 07 — `.json`, 12 keys: 1.21.1 through 26.3

## Upcoming Marathi-inclusive 1.0.1 (not yet published)

The existing 1.0.1 baseline has been extended with a complete **Marathi (`mr_in`) Controlling translation** (12 keys). The 126 previously included languages and all original loader classes remain unchanged. The new JAR is prepared in [release-candidates/1.0.1](release-candidates/1.0.1/), alongside a **separate Minecraft 26.3 Marathi resource pack** based directly on the user's Beyond & More 26.1.2 Marathi translations.

The Minecraft resource pack includes all **8,559 official Minecraft 26.3 English keys**: 7,790 unchanged-key translations reused directly from Beyond & More, 45 reuses of identical English meanings, 2 curated fixes and 722 machine-assisted translations for new/changed English keys. Native-speaker proofreading and real game tests remain outstanding; these files are **not an already-published Marathi release**.

See [installation, provenance, build and verification details](docs/MARATHI_1_0_1.md). Only the companion ZIP targets Minecraft 26.3 specifically; the Controlling JAR retains its pre-existing 1.21.9–26.3 declared range.

## Compatibility model

This project is versioned by localization generation rather than by every individual Controlling release. Minecraft versions that share the same upstream localization schema can reuse the same translation source.

The exact compatibility matrix is generated from audits of the official Controlling repository.

## Upstream priority

For every supported Minecraft version and locale:

1. Controlling's own official translation is authoritative.
2. Controlling Language Expansion fills only missing keys.
3. When Controlling later adds an official key, the corresponding fallback should be removed from this project.

## Attribution

Controlling is created by Jaredlll08 and contributors and is licensed under the MIT License.

- Upstream project: https://github.com/jaredlll08/Controlling
- CurseForge: https://www.curseforge.com/minecraft/mc-mods/controlling

This project is unofficial and is not affiliated with or endorsed by the Controlling developers.

## License

Project code and original localization work in this repository are released under the MIT License. Upstream material remains subject to its original copyright and license.
