# Architecture

Controlling Language Expansion is designed around localization generations, not one translation copy per Minecraft release.

## Core rules

1. Official Controlling translations always win.
2. This project only supplies missing locale keys.
3. Translation text is stored centrally and reused when the upstream English meaning is unchanged.
4. Minecraft versions are grouped only when their upstream localization schema is equivalent.
5. Legacy `.lang` and modern `.json` formats are generated from the same canonical translation source.
6. A locale is only targeted when that locale exists in the corresponding Minecraft Java version.

## Repository layout

- `translations/` — canonical locale dictionaries maintained by this project.
- `data/` — version/locale metadata and generated upstream audits.
- `scripts/` — auditing, generation and validation tools.
- `docs/` — architecture and project documentation.
- `dist/` — generated release artifacts; never committed.

## Upstream generations

The upstream audit computes fingerprints from:

- localization file format (`lang` or `json`),
- ordered key/value content,
- key set,
- official locale files present in the same upstream branch.

Branches with the same English localization content can share one translation generation even if the Minecraft version differs.

## Canonical translations

Canonical translation files use modern lowercase locale identifiers where Minecraft supports them, for example `fr_fr.json`, `id_id.json`, `uk_ua.json`.

The generator is responsible for converting the output filename/casing required by legacy versions, such as `fr_FR.lang`.

Canonical files may contain the union of all known Controlling translation keys. A target build selects only keys required by that upstream generation.

## Fallback generation

For each Minecraft version and locale:

`fallback keys = English upstream keys - official translated keys`

If the official locale is complete, no fallback localization file is generated for that locale.

If the official locale is absent, the project may provide the complete translated key set for that generation.

## Validation goals

Every generated target must verify:

- no invented keys,
- no stale keys,
- no unnecessary overlap with official Controlling translations,
- complete effective coverage for advertised locales,
- valid JSON or `.lang` syntax,
- preserved placeholders and formatting tokens,
- locale validity for the target Minecraft version,
- correct resource path and filename casing.
