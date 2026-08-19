---
name: Font submission
about: Upload and add or update one CJK font family
title: "feat: add <font display name>"
labels: []
assignees: []
---

## Summary

- Stable family ID: `FamilyId`
- English display name:
- Optional localized names or description:
- Change type: <!-- Add / Update / Remove -->
- Languages: <!-- zh-Hans / zh-Hant / ja -->
- Category: <!-- sans-serif / serif / rounded-sans / handwriting / fangsong / display -->

## Font file and source

- Font file path: `community-fonts/<FamilyId>/<file.ttf|file.otf|file.zip>`
- Regular/static instance: <!-- Regular 400, or axes such as wght=400 -->
- ZIP archive member, if applicable:
- Source homepage or repository URL, if available:

## Coverage and rendering

- [ ] The file covers every language listed in `languages`.
- [ ] The submitted face is Regular/400, or the static axes are listed above.
- [ ] `force_autohint` is omitted/`false`, or the need for FreeType auto-hinting is explained below.

Rendering notes:

## Repository changes

- [ ] I read [`CONTRIBUTING.md`](../../CONTRIBUTING.md).
- [ ] This PR changes one font family.
- [ ] The uploaded file is under `community-fonts/<FamilyId>/` and does not use Git LFS.
- [ ] I added or updated the matching entry in `config/fonts.yaml`.
- [ ] I did not commit generated `.cpfont` files, `dist/`, caches, or executables.

## Screenshots or specimens

<!-- Optional. Attach a specimen or render if it helps review the font. -->
