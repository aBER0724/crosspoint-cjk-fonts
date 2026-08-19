# CrossPoint CJK Fonts

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

Optional CJK `.cpfont` files for CrossPoint Reader.

## Submit a font

**Start here: [read the font contribution guide](CONTRIBUTING.md).**

The short version:

1. Fork the repository and create one branch for one font family.
2. Upload one TTF, OTF, or ZIP source file under `community-fonts/<FamilyId>/`.
3. Add one entry to [`config/fonts.yaml`](config/fonts.yaml) with the stable ASCII family ID, localized names, language coverage, category, uploaded file path, and optional license type.
4. Add a short row to [`LICENSES.md`](LICENSES.md). Choose **Commercial use allowed**, **Personal use only**, or leave the license type blank when it is unknown or not provided.
5. Run the configuration tests and, when FreeType is available, a single-family build.
6. Open a pull request. GitHub pre-fills the root checklist; a dedicated **Font submission** choice is also available under `compare` → `New pull request` → `Get started`.

Original upstream repositories, OFL licensing, immutable download URLs, and SHA-256 source locks are not required for uploaded community fonts. Third-party download sources are allowed. The submitter is responsible for the accuracy of the license declaration and for having permission to upload and redistribute the file.

Do not commit generated `.cpfont` files, `dist/`, caches, executables, or Git LFS objects. One pull request must add, update, or remove only one family.

## Catalog

The current catalog contains 16 families for Simplified Chinese, Traditional Chinese, and Japanese. Pages shows each family's original/localized name for the selected UI language and keeps the stable ASCII build ID below it; search accepts either form. Each family is rendered at the seven catalog sizes defined once in [`config/fonts.yaml`](config/fonts.yaml): UI fallback at 8/10/12 pt and reader text at 14/16/18/22 pt.

- 8/10/12 pt provide CJK UI fallback glyphs.
- 14/16/18/22 pt map to the reader's four persisted size slots and show roughly 16/14/12/10 full-width CJK characters per line at the default portrait margin.
- The firmware selects an installed physical file; it never scales a CJK font on the device.

See [`LICENSES.md`](LICENSES.md) for the license type and any source or attribution information provided for each family.

## Local build

Requirements:

- Python 3.11
- FreeType development/runtime libraries

```bash
python -m pip install -r requirements.txt
python scripts/validate_config.py
python scripts/fetch_fallback.py
python scripts/build_fonts.py --clean
python scripts/verify_release.py dist
```

For a quick smoke test:

```bash
python scripts/build_fonts.py --clean --only NotoSansSC
```

Generated files are written under `dist/` and are ignored by Git.

## Local Pages build

The Pages generator needs the published manifest and only the three preview sizes for each family:

```bash
mkdir -p release-assets .cache/pages-fonts
python -c "import urllib.request; urllib.request.urlretrieve('https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/fonts.json', 'release-assets/fonts.json')"
python scripts/fetch_release_previews.py \
  --manifest release-assets/fonts.json \
  --output .cache/pages-fonts \
  --sizes 14,18,22
python scripts/build_pages.py \
  --manifest release-assets/fonts.json \
  --fonts .cache/pages-fonts \
  --output site-dist
```

Open `site-dist/index.html` through a local static HTTP server. The generated `catalog.json` is web schema 1 and records `.cpfont` version 4 plus Release manifest version 2.

## GitHub Actions

- **Build font catalog** validates configuration, Python code, uploaded font paths, the `.cpfont v4` parser, preview renderer, Pages projection, and workflows on relevant pull requests and `main` pushes. Manual smoke runs may select one family.
- **Publish font release** runs after relevant changes reach `main`, builds new or changed families, reuses unchanged published files, verifies the complete asset inventory, and updates the fixed `sd-fonts-m2-b4` Release.
- **Deploy font catalog** generates the 14/18/22 pt PNG previews and deploys the Pages catalog after a successful font release.

Stable device endpoints:

```text
https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/fonts.json
https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/<Family>_<size>.cpfont
```

## Generated asset policy

Uploaded TTF, OTF, and ZIP source files belong under `community-fonts/<FamilyId>/`. Do not commit generated `.cpfont` files, `dist/`, caches, `fonts.json`, or `site-dist/`.
