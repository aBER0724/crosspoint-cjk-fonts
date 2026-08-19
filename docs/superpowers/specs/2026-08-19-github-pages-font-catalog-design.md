# GitHub Pages Font Catalog Design

## Status and scope

This specification defines the public web catalog for `aBER0724/crosspoint-cjk-fonts`. It is intentionally separate from the firmware download endpoint and from community-submission automation.

The deliverable is a static GitHub Pages site at:

```text
https://aber0724.github.io/crosspoint-cjk-fonts/
```

The site presents the current `.cpfont` version 4 catalog described by `fonts.json` schema version 2. GitHub Release remains the binary distribution channel; Pages hosts only HTML, CSS, JavaScript, JSON metadata, and compact previews.

## Goals

- Make every published CJK family discoverable in a browser.
- Render preview images from the actual 2-bit glyph bitmaps stored in `.cpfont v4` files.
- Expose direct Release downloads for all physical sizes: `8 / 10 / 12 / 14 / 16 / 18 / 22 pt`.
- Publish a stable machine-readable `catalog.json` that Font Maker can consume.
- Keep the Pages artifact small enough that it does not become a second font CDN.
- Preserve the existing Release manifest and firmware behavior without changes.

## Non-goals

- Pages does not host the full `.cpfont` files.
- Pages does not replace the device-facing `fonts.json` endpoint.
- The first version does not provide arbitrary browser-side text rendering from `.cpfont`.
- The first version does not implement community submission, legal review, or takedown workflows.
- The first version does not change the existing Release tag or schema versions.

## Alternatives considered

### Recommended: generated static catalog with real bitmap previews

A Python generator reads `config/fonts.yaml`, a verified `fonts.json`, and the published `.cpfont` files. It emits static pages, a web-specific catalog, and PNG previews. This keeps the public site deterministic and ensures the preview matches device data.

### Rejected: load upstream TTF/OTF with `@font-face`

This is visually convenient but does not reflect FreeType hinting, fallback glyph selection, 2-bit quantization, glyph metrics, or the physical bitmap files used by the device.

### Rejected: load `.cpfont` files in every visitor's browser

Downloading several multi-megabyte files only to browse the catalog wastes bandwidth and memory. A future detail page may load one selected file on demand, but it is not required for the first release.

## Source-of-truth boundaries

- `config/fonts.yaml` owns editorial metadata and the shared size groups.
- Release `fonts.json` owns published filenames, sizes, SHA-256 values, styles, and the binary base URL.
- `.cpfont` headers and data sections own the rendered glyphs and metrics.
- The generated web `catalog.json` is a projection. It must not become an independently edited source.

The generator fails instead of silently publishing when these sources disagree.

## Static site structure

Source files live under `pages/` and generated output is written to `site-dist/`:

```text
pages/
├── index.html
├── assets/
│   ├── app.css
│   └── app.js
└── samples.json

site-dist/
├── index.html
├── catalog.json
├── assets/
│   ├── app.css
│   └── app.js
└── previews/
    ├── NotoSansSC_14.png
    ├── NotoSansSC_18.png
    └── NotoSansSC_22.png
```

`site-dist/` is generated and ignored by Git. The deployed Pages artifact contains no `.cpfont`, TTF, OTF, archive, or executable file.

## Web catalog schema

`catalog.json` uses an explicit web schema independent of the firmware manifest:

```json
{
  "schemaVersion": 1,
  "cpfontVersion": 4,
  "manifestVersion": 2,
  "siteUrl": "https://aber0724.github.io/crosspoint-cjk-fonts/",
  "manifestUrl": "https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/fonts.json",
  "fontMakerUrl": "https://github.com/aBER0724/crosspoint-cjk-font-maker",
  "previewSizes": [14, 18, 22],
  "families": []
}
```

Each family contains:

- `name`
- `description`
- `styles`
- `sourceUrl`
- `files[]` with `name`, `physicalSize`, `byteSize`, `sha256`, and `downloadUrl`
- `previews` keyed by physical size


## `.cpfont v4` parser

A focused Python module owns binary parsing. It validates before exposing data:

- magic is `CPFONT\0\0`;
- version is exactly `4`;
- global header is 32 bytes;
- style TOC entries are 32 bytes;
- every style ID is valid and unique;
- interval, glyph, kerning, ligature, and bitmap section boundaries stay inside the file;
- interval glyph offsets and glyph counts agree;
- every glyph bitmap range stays inside its style bitmap section.

The parser exposes immutable header, interval, glyph, and bitmap records. Manifest generation and preview generation should reuse this parser rather than maintaining separate partial header readers.

## Real bitmap preview rendering

The generator renders only `preview_sizes: [14, 18, 22]` and uses the regular style. The preview text is fixed and stored in `pages/samples.json`, with Simplified Chinese, Traditional Chinese, Japanese, Latin, punctuation, and digits.

Rendering follows device data:

1. Locate each Unicode code point through the `.cpfont` interval table.
2. Read its 16-byte glyph record.
3. Interpret `advanceX` as unsigned 12.4 fixed point.
4. Position the glyph using `left`, `top`, ascender, and baseline metrics.
5. Decode the linear 2-bit bitmap, four pixels per byte, most-significant pair first.
6. Map values `0 / 1 / 2 / 3` to four fixed grayscale tones.
7. Wrap lines to a deterministic canvas width using physical advances.
8. Write a compact PNG using Pillow.

Missing glyphs are rendered as the font's U+FFFD glyph when available. If neither the requested glyph nor U+FFFD is usable, the preview generator records the missing code point and continues; it fails only when the resulting preview contains no renderable glyphs.

The renderer must not use the source TTF/OTF or browser fonts.

## User interface

The first page is an editorial card grid rather than a large application shell.

Each card shows:

- family name and description;
- the selected real bitmap preview;
- a `14 / 18 / 22 pt` preview selector;
- seven direct Release download links with human-readable sizes;
- source links when present;
- an “Open Font Maker” secondary action.

Global controls provide:

- text search over name and description;
- language/region tags derived from catalog metadata when available;
- style/category filters when metadata provides them;
- browser-language default for Chinese, Japanese, or English UI;
- a persistent manual locale override in `localStorage`.

No family ZIP is required. Direct links always use the URL already represented by the published manifest base URL and filename.

## Failure behavior

Generation fails on:

- manifest schema other than `2`;
- `.cpfont` version other than `4`;
- missing preview-size file;
- filename, byte size, or SHA-256 disagreement;
- unsafe output paths;
- malformed binary section boundaries;
- an empty family list.

The browser UI handles individual broken preview images without hiding download metadata. A catalog fetch failure in Font Maker is handled by Font Maker and does not change this site's artifact.

## GitHub Pages deployment

A dedicated `.github/workflows/deploy-pages.yml` supports `workflow_dispatch` and deployment after a successful versioned Release publication.

The job:

1. checks out trusted repository code;
2. installs pinned Python dependencies;
3. downloads and verifies Release `fonts.json`;
4. downloads only the three preview sizes for each family into a cache directory;
5. verifies file size and SHA-256 before parsing;
6. builds `site-dist/`;
7. runs catalog and HTML smoke tests;
8. uploads a Pages artifact;
9. deploys with `actions/deploy-pages`.

Permissions are limited to `contents: read`, `pages: write`, and `id-token: write`. The workflow never executes code from a pull-request checkout and does not use `pull_request_target`.

The repository Pages source is GitHub Actions. This deployment is a catalog only; it does not restore the removed device font mirror.

## Testing

Python unit tests use small synthetic `.cpfont v4` fixtures and cover:

- valid header and regular-style parsing;
- rejection of bad magic, wrong version, truncated TOC, and out-of-range sections;
- Unicode interval lookup;
- 2-bit decoding order;
- glyph placement and grayscale preview output;
- web catalog URLs, sizes, hashes, and preview-size completeness;
- generated HTML containing no `.cpfont` payload or external executable script.

A release smoke test downloads one known published file and compares the generated preview path and checksum-derived catalog entry. Network-dependent smoke tests remain separate from deterministic unit tests.

## Documentation updates

`README.md` and `DESIGN.md` will describe:

- the Pages URL;
- the distinction between Pages previews and Release downloads;
- the web catalog schema;
- how to run a local site build;
- why real `.cpfont` previews are used;
- that Pages is not a device-compatible binary mirror.

## Acceptance criteria

- The deployed URL loads without a build tool in the browser.
- All current families appear.
- Every family exposes exactly seven Release downloads.
- Every family exposes real previews at 14, 18, and 22 pt.
- Preview pixels are decoded from `.cpfont v4`, not rendered from source fonts.
- `catalog.json` reports `.cpfont` version 4 and manifest version 2.
- The Pages artifact contains no `.cpfont`, TTF, OTF, or archives.
- Existing catalog configuration validation and Release verification continue to pass.
