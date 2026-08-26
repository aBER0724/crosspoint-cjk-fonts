# CrossPoint CJK Fonts

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

Optional CJK `.cpfont` files for CrossPoint Reader.

## Submit a font

**Start here: [read the font contribution guide](CONTRIBUTING.md).**

The short version:

1. Fork the repository. Keep each font PR to one family.
2. Put one TTF, OTF, or ZIP file under `community-fonts/<FamilyId>/`.
3. Add its names, languages, category, and file path to [`config/fonts.yaml`](config/fonts.yaml). A font homepage or source repository URL is optional.
4. Open a pull request. GitHub pre-fills the checklist, or you can choose the **Font submission** template.

The [contribution guide](CONTRIBUTING.md) has the field table and full examples. Do not commit generated `.cpfont` files, `dist/`, caches, executables, or Git LFS objects.

## Catalog

The current catalog contains 16 families for Simplified Chinese, Traditional Chinese, and Japanese. Pages shows each family's original/localized name for the selected UI language and keeps the stable ASCII build ID below it; search accepts either form. Catalog metadata can classify a family as `reader` (the default) or `ui`.

- UI families are presented as **UI font** families instead of exposing separate 8/10/12 pt download buttons.
- Reader families expose their configured reader sizes while keeping the fixed 8/10/12 pt UI fallback files out of the download-button list.
- The standard catalog build still emits 8/10/12 pt for CJK UI fallback and 14/16/18/22 pt for reader text.
- 14/16/18/22 pt map to the reader's four persisted size slots and show roughly 16/14/12/10 full-width CJK characters per line at the default portrait margin.
- The firmware selects an installed physical file; it never scales a CJK font on the device.

For private font conversion, [CrossPoint CJK Font Maker](https://github.com/aBER0724/crosspoint-cjk-font-maker) produces a single `.cpfontpkg` family package. The package keeps one `.cpfont v4` file per physical size, always includes UI sizes 8/10/12 pt, and accepts a custom positive-integer reader-size list (default 14/16/18/22 pt).

See [`SOURCES.md`](SOURCES.md) for the source links recorded for each family.

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

Self-builders can emit only the sizes their device needs instead of the full catalog contract:

```bash
python scripts/build_fonts.py --clean --only NotoSansSC --sizes 12,14,18,22
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

- **Build font catalog** validates configuration, Python code, uploaded font paths, the `.cpfont v4` parser, preview renderer, Pages projection, and workflows on relevant pull requests and `main` pushes. Manual runs may select one family (`smoke_family`), override the physical sizes (`sizes`, comma-separated), and choose a `mode` (`manual` / `self` / `contribute`) for a self-built catalog, a personal Release, or an upstream submission.
- **Publish font release** runs after relevant changes reach `main`, builds new or changed families, reuses unchanged published files, verifies the complete asset inventory, and updates the fixed `sd-fonts-m2-b4` Release.
- **Deploy font catalog** generates the 14/18/22 pt PNG previews and deploys the Pages catalog after a successful font release.

### Manual font build

To build a catalog from the Actions UI:

1. Open the **Actions** tab and select the **Build font catalog** workflow.
2. Click **Run workflow**.
3. Fill in the inputs below, then click **Run workflow** again.

| Input | Default | Effect |
| --- | --- | --- |
| `smoke_family` | empty | Build only this one family for a fast smoke run; empty builds every family. |
| `sizes` | empty | Comma-separated physical sizes to emit, e.g. `12,14,18`; empty uses the seven catalog sizes from `config/fonts.yaml`. |
| `mode` | `manual` | `manual` builds only (no publishing); `self` also publishes this repo's `sd-fonts-m2-b4` Release; `contribute` validates, then pushes a submit branch for a PR to upstream. |

A malformed `sizes` value (empty list, non-integer, zero, or negative) fails the run before any font is built.

#### Scenario 1 — build fonts for your own device (`mode: self`)

Runs on your own fork, the built catalog is published to **your** `sd-fonts-m2-b4` Release and the manifest `baseUrl` points at your repository:

1. Fork this repository and push your font sources under `community-fonts/<FamilyId>/` on the default branch.
2. Run **Build font catalog** with `mode: self` (optionally `smoke_family` and `sizes`).
3. When the run finishes, the Release at `https://github.com/<your-owner>/<your-repo>/releases/tag/sd-fonts-m2-b4` holds `fonts.json` plus every `.cpfont`.
4. On the device, set the font repository to `<your-owner>/<your-repo>` (empty keeps the upstream default) and download fonts.

Repeat runs update the same Release assets (`--clobber`), so your device URL never changes.

#### Scenario 2 — submit a font to upstream (`mode: contribute`)

GitHub's `GITHUB_TOKEN` cannot open a cross-repo PR from a fork, so the flow is semi-automatic: the run validates and builds your font, pushes a `submit/<FamilyId>` branch to your fork, then prints a link you click to open the PR draft:

1. Fork this repository and push your font sources under `community-fonts/<FamilyId>/` on the default branch.
2. Run **Build font catalog** with `mode: contribute` (use `smoke_family: <FamilyId>` to validate just your font).
3. After the run, open the **Summary** tab and click the printed compare link to create a PR draft to upstream. Follow [`CONTRIBUTING.md`](CONTRIBUTING.md).

Stable device endpoints:

```text
https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/fonts.json
https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/<Family>_<size>.cpfont
```

## Generated asset policy

Uploaded TTF, OTF, and ZIP source files belong under `community-fonts/<FamilyId>/`. Do not commit generated `.cpfont` files, `dist/`, caches, `fonts.json`, or `site-dist/`.
