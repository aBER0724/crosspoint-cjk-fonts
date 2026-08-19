# CrossPoint CJK Fonts

Reproducible build and GitHub Release hosting for optional CrossPoint Reader CJK `.cpfont` files.

The generated binaries are deliberately excluded from Git history. GitHub Actions downloads SHA-256-locked upstream font sources, converts them into device-native files, generates `fonts.json`, verifies every asset, and publishes the catalog as the `sd-fonts-m2-b4` Release.

A lightweight browser catalog is generated for GitHub Pages at:

```text
https://aber0724.github.io/crosspoint-cjk-fonts/
```

Pages contains only HTML, JSON metadata, and compact PNG previews decoded from the real `.cpfont v4` 2-bit bitmaps. All font downloads continue to point directly at the versioned GitHub Release.

## Catalog

The current catalog contains 15 OFL-1.1 families for Simplified Chinese,
Traditional Chinese, and Japanese. Pages shows each family's original/localized
name for the selected UI language and keeps the stable ASCII build ID below it;
search accepts either form. Each family is pre-rendered at the seven
catalog sizes defined once in [config/fonts.yaml](config/fonts.yaml): UI
fallback at 8/10/12 pt and reader text at 14/16/18/22 pt.

- 8/10/12 pt provide CJK UI fallback glyphs.
- 14/16/18/22 pt map to the reader's four persisted size slots and show roughly
  16/14/12/10 full-width CJK characters per line at the default portrait margin.
- The firmware selects an installed physical file; it never scales a CJK font on the device.

See [LICENSES.md](LICENSES.md) for exact upstream sources and attribution.

## Reproducibility

Source URLs and expected SHA-256 digests live in [config/fonts.yaml](config/fonts.yaml). A build stops before conversion if a downloaded source does not match its lock.

The Latin fallback used to fill punctuation and basic Latin glyphs is also SHA-256 locked by [scripts/fetch_fallback.py](scripts/fetch_fallback.py).

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

- **Build font catalog** validates configuration, Python code, the `.cpfont v4` parser, preview renderer, Pages projection, and workflows on every relevant pull request and `main` push. Font binaries are built only by manual dispatch or reusable workflow calls, so a normal `main` validation does not duplicate the Release build.
- **Publish font release** is manual and requires typing `sd-fonts-m2-b4`. It performs a clean full build, verification, and replacement of the versioned Release assets.
- **Deploy font catalog** runs manually or after a successful font release. It downloads and verifies only the 14/18/22 pt files, generates 45 PNG previews, and deploys a font-free Pages artifact.

The stable device endpoints are:

```text
https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/fonts.json
https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/<Family>_<size>.cpfont
```

The public repository and Release are the production distribution channel. For local development, the firmware's test override can instead point to a LAN HTTP server serving an already verified `release-assets/` directory.

## Generated asset policy

Do not commit `.cpfont`, downloaded source fonts, caches, `fonts.json`, or `site-dist/`. Release assets are the binary distribution channel. Pages is a human-readable catalog and real-bitmap preview layer, not a device font mirror or alternate font CDN.
