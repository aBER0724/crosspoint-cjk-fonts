---
name: Font submission
about: Add or update one CJK font family in the public catalog
title: "feat: add <font display name>"
labels: []
assignees: []
---

## Summary

<!-- One pull request must add or update exactly one family. Briefly explain why it is useful for CrossPoint Reader. -->

- Stable family ID: `FamilyId`
- Display name:
- Change type: <!-- Add / Update / Remove -->
- Languages: <!-- zh-Hans / zh-Hant / ja -->
- Category: <!-- sans-serif / serif / rounded-sans / handwriting / fangsong / display -->

## Authoritative source

- Upstream project:
- Pinned release or full commit SHA:
- Exact source font or archive URL:
- Source SHA-256:
- Regular/static instance: <!-- e.g. Regular 400, or wght=400 -->
- Archive member, if applicable:

## License review

- License: `OFL-1.1`
- Pinned license URL:
- Copyright holder(s):
- Reserved Font Name declared? <!-- No / Yes: list it -->
- Additional permission or naming consideration:

<!-- Do not rely only on a third-party font index. Link the original upstream license and explain any OFL naming condition. -->

## Coverage and rendering

- [ ] The source actually covers every language declared in `languages`.
- [ ] The submitted face is the normal Regular/400 style.
- [ ] `force_autohint` is omitted, or its visual need is explained below.
- [ ] I checked representative CJK punctuation, Latin text, and numbers.

Rendering notes:

<!-- Mention unusual metrics, missing glyphs, autohint requirements, or other visible limitations. -->

## Repository changes

- [ ] I read [`CONTRIBUTING.md`](../../CONTRIBUTING.md).
- [ ] This PR changes only one font family.
- [ ] I added or updated the family in `config/fonts.yaml`.
- [ ] I added or updated its attribution in `LICENSES.md`.
- [ ] The source URL is pinned to a tag or full commit, not a moving branch or `latest` URL.
- [ ] The SHA-256 is for the exact downloaded source URL.
- [ ] I did not commit TTF/OTF/ZIP sources, generated `.cpfont` files, `dist/`, caches, executables, or Git LFS objects.

## Validation

- [ ] `python scripts/validate_config.py`
- [ ] `python -m py_compile scripts/*.py`
- [ ] `python -m unittest discover -s tests -v`
- [ ] `python scripts/fetch_fallback.py`
- [ ] `python scripts/build_fonts.py --clean --only <FamilyId>`
- [ ] `python scripts/verify_release.py dist`

If the full FreeType build was not run locally, explain why:

<!-- Maintainers can trigger a trusted single-family build after source and license review. -->

## Screenshots or specimens

<!-- Optional but useful. Attach an upstream specimen or local render that demonstrates the declared language coverage. Do not upload the source font itself. -->
