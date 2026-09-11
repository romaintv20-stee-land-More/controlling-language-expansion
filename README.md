# Controlling Language Expansion

**Controlling Language Expansion** is an unofficial localization companion for **Controlling** by Jaredlll08.

Its goal is to extend Controlling's language support to as many languages available in Minecraft Java Edition as possible, across both legacy and modern Minecraft versions.

The original **Controlling** mod is still required. This project only provides additional localization resources and does not replace or modify Controlling's gameplay features.

## Features

- Adds translations for languages missing from Controlling.
- Completes partially translated languages when some Controlling strings are missing.
- Always gives priority to Controlling's official translations.
- Supports languages according to their actual availability in each Minecraft version.
- Includes selected special Minecraft languages when relevant.
- Lightweight and client-side.
- Supports both legacy `.lang` files and modern `.json` localization files.
- Provides version-specific builds covering multiple generations of Minecraft and Controlling.
- Reuses translations between versions when the upstream English meaning is identical.
- Avoids inventing unsupported localization keys or fake language support.

## Current Version Support

The project now provides release coverage from **Minecraft 1.7.10 through Minecraft 26.2**, using individual or grouped builds where the localization payload is compatible.

Current release coverage:

- Minecraft 1.7.10
- Minecraft 1.8.9
- Minecraft 1.10.2
- Minecraft 1.11.2
- Minecraft 1.12.2
- Minecraft 1.13.2-1.14.2
- Minecraft 1.15.2
- Minecraft 1.16.5
- Minecraft 1.17.1
- Minecraft 1.18.2
- Minecraft 1.19.2
- Minecraft 1.19.3
- Minecraft 1.19.4
- Minecraft 1.20-1.20.4
- Minecraft 1.20.5-1.21.8
- Minecraft 1.21.9-26.2

Older branches use dedicated compatibility builds when Minecraft, Forge, or localization formats differ significantly. Newer releases are grouped only when the same localization payload can be safely shared across versions.

Minecraft 1.19 and 1.19.1 are not currently advertised by the project and may be reviewed separately for compatibility with the existing 1.19-generation build.

## Translation Policy

Controlling's own translations always have priority.

If Controlling already provides a complete translation for a language, Controlling Language Expansion does not unnecessarily replace it.

If a translation is incomplete or missing, this project provides the missing strings whenever possible.

The project avoids inventing unsupported localization keys and only targets languages that actually exist in the corresponding Minecraft Java Edition version.

For modern versions, some very low-resource or special community languages may intentionally remain on English fallback when a reliable translation cannot be produced with sufficient confidence.

## Translation Method

Some missing translations in Controlling Language Expansion are generated or assisted by AI, especially for languages where no reliable existing Controlling translation is available.

Existing official translations from Controlling always have priority and are not replaced unnecessarily.

AI-assisted translations are treated as best-effort localization and may be improved over time based on community feedback and corrections from native speakers.

## Compatibility

Each release is built for a specific Minecraft version or a compatible group of versions depending on Controlling's localization format, Minecraft resource-pack format, loader support, Java version, and upstream changes.

Older versions use Minecraft's legacy `.lang` localization format, while newer versions use `.json` language files.

The addon is designed to remain lightweight and client-side only.

## Requirements

You must install the original **Controlling** mod for your Minecraft version.

Controlling Language Expansion does not include Controlling itself.

Some newer Controlling versions may also require dependencies used by the original mod. Always follow the dependency requirements listed on the Controlling project page for your Minecraft version.

## Installation

1. Install the correct mod loader for your Minecraft version.
2. Install **Controlling**.
3. Download the matching version of **Controlling Language Expansion**.
4. Place both mods in your Minecraft `mods` folder.
5. Launch the game and select your language normally from Minecraft's language settings.

No additional configuration is required.

## Upstream Audit

The project audits the version-numbered Controlling branches from Minecraft 1.7.10 through 26.2 and tracks localization changes across seven historical generations.

Across the audited history, Controlling uses only 15 unique English localization keys relevant to this expansion project. Official upstream translations remain authoritative for every version and locale.

## Credits

**Controlling** is created by **Jaredlll08** and contributors.

This is an independent, unofficial localization project and is not affiliated with or endorsed by the original Controlling developer.

- Original Controlling project: https://www.curseforge.com/minecraft/mc-mods/controlling
- Upstream source: https://github.com/jaredlll08/Controlling
- Controlling Language Expansion source: https://github.com/romaintv20-stee-land-More/controlling-language-expansion

## License

Controlling Language Expansion is released under the **MIT License**.

Project code and original localization work are released under the MIT License. Any upstream material remains subject to its original copyright and license.
