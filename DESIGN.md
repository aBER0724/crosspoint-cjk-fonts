# CrossPoint CJK Fonts

## Approved reader-size contract

- UI fallback files: `8 / 10 / 12 pt`
- Reader files: `14 / 16 / 18 / 22 pt`
- Web preview files: `14 / 18 / 22 pt`
- Reader persisted slots remain `0 / 1 / 2 / 3`.
- Current complete packs map to `14 / 16 / 18 / 22`.
- Existing complete `12 / 14 / 16 / 18` packs keep their legacy mapping.
- UI fallback files must not shift reader slot selection.
- CJK fonts are never scaled on-device.

At the default portrait margin, NotoSansSC represents approximately `16 / 14 / 12 / 10` full-width CJK characters per ordinary body-text line. EPUB margins and first-line indentation can reduce these counts.

## Repository identity

- Target repository: `aBER0724/crosspoint-cjk-fonts`
- Release tag: `sd-fonts-m2-b4`
- Firmware manifest endpoint:
  `https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/fonts.json`
- Generated binaries stay out of Git history.
- Remote creation, push, Release publication, and Pages deployment require separate explicit approval.

## Catalog configuration

`config/fonts.yaml` defines the shared groups once:

```yaml
ui_sizes: [8, 10, 12]
reader_sizes: [14, 16, 18, 22]
preview_sizes: [14, 18, 22]
```

Every family builds the ordered union `8/10/12/14/16/18/22`.

## Future GitHub Pages catalog

- Editorial card layout.
- Samples rendered from actual built `.cpfont` data in 1-bit monochrome.
- Simplified Chinese, Traditional Chinese, Japanese, and English UI.
- Browser-language default with a `localStorage` override.
- Seven direct `.cpfont` downloads per family; no family ZIP.
- Secondary custom-font CTA configured by `FONT_MAKER_URL`.
- Default CTA target until a public app exists:
  `https://github.com/aBER0724/xteink-cjk-font-maker`
- Do not claim Font Maker exports `.cpfont` v4; its current outputs are `legacy-bin` and experimental `xbf2`.

## Future community submissions

- One source record under `community-fonts/<name>.yml`.
- First version remains OFL-1.1-only.
- Require pinned TTF/OTF source, SHA-256, license, and source metadata.
- PR CI is read-only, uses no Secrets, and does not use `pull_request_target`.
- PRs produce temporary build and preview artifacts only.
- Production publication stays maintainer-reviewed and manually confirmed.
- Private or non-redistributable fonts remain in the personal Font Maker flow.
- Any future one-click PR flow must use a server-side minimum-permission GitHub App, never a frontend PAT.
