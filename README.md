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

Early development (`0.1.0-beta` planned). No public release has been published yet.

The initial upstream audit covers all 37 version-numbered Controlling branches from 1.7.10 through 26.2 and currently identifies 7 localization generations with only 15 unique English localization keys across the full audited history.

Current audited generations:

- Generation 01 — `.lang`, 13 keys: 1.7.10, 1.8.9, 1.10.2, 1.12
- Generation 02 — `.lang`, 9 keys: 1.11
- Generation 03 — `.json`, 9 keys: 1.13
- Generation 04 — `.json`, 13 keys: 1.14.2, 1.15, 1.16, 1.17, 1.18, 1.19
- Generation 05 — `.json`, 12 keys: 1.19.3 through 1.20.4
- Generation 06 — `.json`, 14 keys: 1.20.5, 1.20.6, 1.21
- Generation 07 — `.json`, 12 keys: 1.21.1 through 1.21.11, 26.1/26.1.1/26.1.2 and 26.2

The audit is automated; this matrix is expected to evolve if upstream branches change.

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
