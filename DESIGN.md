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

Every family also declares localized reader-facing names without changing its stable build ID:

```yaml
- name: WenKaiCJK
  display_names: {en: "LXGW WenKai", zh: "霞鹜文楷", ja: "LXGW WenKai"}
```

The ASCII `name` continues to define filenames such as `WenKaiCJK_14.cpfont`; Pages uses `display_names` for card titles and search.

## GitHub Pages catalog

- Public URL: `https://aber0724.github.io/crosspoint-cjk-fonts/`
- Web catalog endpoint: `https://aber0724.github.io/crosspoint-cjk-fonts/catalog.json`
- Editorial card layout with Simplified Chinese, Traditional Chinese, Japanese, and English UI.
- Each family keeps its stable ASCII `name` for `.cpfont` filenames and firmware compatibility, while `display_names` provides the reader-facing `en` / `zh` / `ja` title used by Pages.
- The current locale selects the card title; the stable ID remains visible below it, and search matches both localized titles and the ID.
- Preview PNGs are rendered from actual built `.cpfont v4` 2-bit bitmap data at 14/18/22 pt.
- The preview renderer uses stored intervals, glyph metrics, fp4 advances, kerning, ligatures, baseline, and fallback behavior. It does not render the source TTF/OTF.
- Browser-language default with a `localStorage` override.
- Seven direct Release `.cpfont` downloads per family; no family ZIP and no binary copy on Pages.
- Secondary custom-font CTA target: `https://crosspoint-cjk-font-maker.onrender.com/`.
- Font Maker's approved current-format workflow is specified separately; its existing `legacy-bin` and experimental `xbf2` outputs remain legacy tools until that implementation is deployed.
- Pages is not a device-compatible binary mirror. The firmware manifest endpoint remains the versioned GitHub Release.

## Future community submissions

- One source record under `community-fonts/<name>.yml`.
- First version remains OFL-1.1-only.
- Require pinned TTF/OTF source, SHA-256, license, and source metadata.
- PR CI is read-only, uses no Secrets, and does not use `pull_request_target`.
- PRs produce temporary build and preview artifacts only.
- Production publication stays maintainer-reviewed and manually confirmed.
- Private or non-redistributable fonts remain in the personal Font Maker flow.
- Any future one-click PR flow must use a server-side minimum-permission GitHub App, never a frontend PAT.
