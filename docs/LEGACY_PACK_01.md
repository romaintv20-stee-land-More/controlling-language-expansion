# Legacy Pack 01 — Minecraft 1.7.10 to 1.12.2

Targets: 1.7.10, 1.8.9, 1.10.2, 1.11.2 and 1.12.2.

The audit found 97 unique Minecraft locale IDs across these targets.

## Translation sources

Priority: target Controlling official translation, then an official Controlling 1.12 donor when the English meaning is unchanged, then a canonical Controlling Language Expansion translation, then a documented regional/base-locale alias. `en_us` fallback is used only when the intended text is intentionally identical to English.

The first pack contains 58 new canonical locale translations and 13 documented aliases/no-op English variants. Combined with Controlling's official legacy translations, this gives usable coverage for 91 of the 97 legacy locale IDs.

## Intentionally excluded special locales

The following six extremely marginal/special locales are intentionally excluded rather than guessed: `gv_im` (Manx), `jbo_en` (Lojban), `qya_aa` (Quenya), `se_no` (Northern Sami), `tlh_aa` (Klingon), and `tzl_tzl` (Talossan).

Reliable Controlling translations for these locales could not be verified and their practical value is expected to be extremely low. They are therefore outside the Pack 01 completion target unless a reliable translation source or native contribution becomes available later.

Controlling already supplies official legacy translations for Pirate Speak (`en_pt`) and, from 1.10.2 onward, Upside Down English (`en_ud`). Shakespearean English (`en_ws`) and LOLCAT (`lol_us`) have canonical translations here.

Generated ZIP files are CI/QA payloads only until the packaging strategy is finalized; no release is published automatically.
