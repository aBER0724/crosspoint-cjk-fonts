---
name: Font submission
about: Upload and add or update one CJK font family
title: "feat: add <font display name>"
labels: []
assignees: []
---

## Summary

<!-- One pull request must add, update, or remove exactly one family. -->

- Stable family ID: `FamilyId`
- Display name:
- Change type: <!-- Add / Update / Remove -->
- Languages: <!-- zh-Hans / zh-Hant / ja -->
- Category: <!-- sans-serif / serif / rounded-sans / handwriting / fangsong / display -->

## Uploaded font

- Font file path: `community-fonts/<FamilyId>/<file.ttf|file.otf|file.zip>`
- Regular/static instance: <!-- e.g. Regular 400, or wght=400 -->
- Archive member, if applicable:
- Download page or source URL, if available:

## License declaration

- License type: <!-- Commercial use allowed / Personal use only / Unknown / not provided -->
- License or terms URL, if available:
- Author or copyright holder, if known:
- Additional notes:

<!-- This is a submitter declaration. An original upstream repository and OFL license are not required. -->

## Coverage and rendering

- [ ] The file actually covers every language declared in `languages`.
- [ ] The submitted face is the normal Regular/400 style.
- [ ] `force_autohint` is omitted, or its visual need is explained below.
- [ ] I checked representative CJK punctuation, Latin text, and numbers.

Rendering notes:

## Repository changes

- [ ] I read [`CONTRIBUTING.md`](../../CONTRIBUTING.md).
- [ ] This PR changes only one font family.
- [ ] I placed the source file under `community-fonts/<FamilyId>/` without Git LFS.
- [ ] I added or updated the family in `config/fonts.yaml`.
- [ ] I added or updated its license declaration or attribution in `LICENSES.md`.
- [ ] I have permission to upload and redistribute the submitted file.
- [ ] I did not commit generated `.cpfont` files, `dist/`, caches, executables, or Git LFS objects.

## Validation

- [ ] `python scripts/validate_config.py`
- [ ] `python -m py_compile scripts/*.py`
- [ ] `python -m unittest discover -s tests -v`
- [ ] `python scripts/fetch_fallback.py`
- [ ] `python scripts/build_fonts.py --clean --only <FamilyId>`
- [ ] `python scripts/verify_release.py dist`

If the full FreeType build was not run locally, explain why:

## Screenshots or specimens

<!-- Optional. Attach a specimen or local render. -->
