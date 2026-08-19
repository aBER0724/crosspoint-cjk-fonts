## Catalog update

This update keeps the stable `sd-fonts-m2-b4` compatibility channel and publishes a complete catalog of **{{ family_count }} font families** and **{{ cpfont_count }} `.cpfont` files** ({{ total_size }}).

All families provide physical **8, 10, and 12 pt UI files** plus **14, 16, 18, and 22 pt reader files**. CrossPoint Reader selects a real installed size and does not scale CJK glyphs on the device.

### Added

- **{{ FamilyId }}** — {{ short reader-facing description }}

### Updated

- **{{ FamilyId }}** — {{ what changed }}

### Removed

- **{{ FamilyId }}** — {{ removal or replacement reason }}

Remove any empty change section before publishing. The automated Release workflow fills these sections from `plan.json`, `fonts.json`, and the previous manifest.

### Installation

Browse previews and download individual physical sizes from the [CrossPoint CJK font catalog](https://aber0724.github.io/crosspoint-cjk-fonts/). Device downloads continue to use this GitHub Release directly.

### Verification

- `fonts.json` is the complete firmware manifest (schema 2).
- `build-index.json` records the reproducible per-family build fingerprints and file hashes.
- Every published `.cpfont` uses binary format 4 and is checked for size, SHA-256, and structure before metadata is updated.
- Source links recorded for each family are available in `FONT-SOURCES.md`.
