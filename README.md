# CrossPoint Fonts

Release hosting metadata for optional CrossPoint Reader `.cpfont` files.

The firmware downloads `fonts.json` and individual font sizes from a GitHub
Release named `sd-fonts-m2-b4`. Generated font binaries are release assets and
are deliberately excluded from Git history. The current prepared release has
15 CJK families, six sizes per family (8, 10, 12, 14, 16, and 18 pt), and 90
`.cpfont` files.

## Source Of Truth

Font selection, source URLs, conversion settings, and public license metadata
live in the firmware repository:

- `lib/EpdFont/scripts/sd-fonts.yaml`
- `lib/EpdFont/scripts/build-sd-fonts.py`
- `scripts/generate-font-manifest.py`

This repository stores release documentation and verification tooling. It does
not replace those build sources.

## Preparing A Release

1. Build the font assets from the firmware repository with its pinned source
   definitions.
2. Generate `fonts.json` with the final GitHub Release download URL.
3. Put `fonts.json` and all `.cpfont` files in `release-assets/`.
4. Run `python scripts/verify_release.py release-assets`.
5. Create the `sd-fonts-m2-b4` GitHub Release and upload the verified files.

Do not commit generated `.cpfont` files to this repository. A release must
contain the license notices referenced by `LICENSES.md`, either as release
notes or as an accompanying notice file.

## Licensing

The generated `.cpfont` files are converted and subsetted derivatives of their
upstream fonts. Their upstream font licenses continue to apply. See
`LICENSES.md` for the exact source and license links used by the current CJK
catalog.

