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
