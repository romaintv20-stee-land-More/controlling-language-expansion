# Canonical translations

This directory will contain the maintained translation source for Controlling Language Expansion.

Rules:

- One canonical file per Minecraft Java locale, using lowercase modern locale IDs where applicable (for example `fr_fr.json`).
- Files may contain the union of known Controlling localization keys across supported generations.
- Generated target files must select only keys that exist in the target Controlling generation.
- Official Controlling translations remain authoritative; generated fallbacks must exclude keys already translated upstream for that target branch.
- Do not add locales that are not actually available in Minecraft Java for the target generation.
- Preserve placeholders, formatting tokens and intended UI meaning.

Legacy filename casing and `.lang` formatting are output concerns handled by the generator, not duplicated translation sources.
