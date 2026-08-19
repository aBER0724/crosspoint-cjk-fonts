# GitHub Pages Font Catalog Implementation Plan

> Execute in `C:/Users/aBER/Documents/Code/crosspoint-cjk-fonts-pages` on `feat/github-pages-font-catalog`. Use test-first changes and commit after each green task.

## Task 1: Canonical `.cpfont v4` parser

**Files**
- Create `scripts/cpfont_v4.py`
- Create `tests/test_cpfont_v4.py`

**Steps**
1. Add synthetic fixture helpers and failing tests for the 32-byte global header, 32-byte style TOC, 12-byte intervals, 16-byte glyph records, codepoint lookup, and 2-bit decode order.
2. Add rejection tests for bad magic, wrong version, duplicate/invalid styles, truncated sections, invalid cumulative interval offsets, invalid bitmap lengths, and out-of-range glyph bitmaps.
3. Implement immutable parser records, boundary checks, regular-style lookup, kerning/ligature accessors, and bitmap decoding.
4. Run `python -m unittest tests.test_cpfont_v4 -v`.
5. Commit: `feat: add validated cpfont v4 parser`.

## Task 2: Real bitmap preview renderer

**Files**
- Create `scripts/render_cpfont_preview.py`
- Create `tests/test_cpfont_preview.py`
- Create `pages/samples.json`
- Update `requirements.txt`

**Steps**
1. Add failing tests for baseline placement, fp4 advances, kerning, ligature substitution, wrapping, replacement-glyph fallback, and exact four-tone grayscale decoding.
2. Pin Pillow and implement deterministic grayscale PNG rendering from parsed `.cpfont` data only.
3. Add the fixed multilingual sample strings used by the catalog.
4. Run `python -m unittest tests.test_cpfont_preview -v`.
5. Commit: `feat: render previews from cpfont bitmaps`.

## Task 3: Web catalog projection and static site build

**Files**
- Create `scripts/build_pages.py`
- Create `scripts/fetch_release_previews.py`
- Create `pages/index.html`
- Create `pages/assets/app.css`
- Create `pages/assets/app.js`
- Create `tests/test_pages_catalog.py`
- Update `.gitignore`

**Steps**
1. Add failing tests for web schema version 1, cpfont version 4, manifest version 2, exactly seven ordered downloads, verified core license status, preview completeness, URL safety, hash/size verification, and an artifact free of fonts/archives/external scripts.
2. Implement manifest/config joins and strict mismatch failures.
3. Implement verified download of only `14/18/22` files with resumable local cache behavior.
4. Implement the static editorial catalog with local assets, search, dynamically available filters, locale selection, real preview-size switching, direct Release downloads, and graceful image failures.
5. Run `python -m unittest discover -s tests -v` and a synthetic site build.
6. Commit: `feat: build static font catalog`.

## Task 4: Pages deployment workflow

**Files**
- Create `.github/workflows/deploy-pages.yml`
- Update `.github/workflows/build-fonts.yml`
- Update `tests/test_catalog_config.py`

**Steps**
1. Add source-level workflow tests for trusted triggers, minimal permissions, preview-only downloads, Pages artifact upload, and no pull-request code execution.
2. Add Pages source files/scripts/tests to PR validation paths and execute the unit suite in the validation job.
3. Add `workflow_dispatch` and successful `workflow_run` deployment after `Publish font release`.
4. Run YAML parse checks and the full unit suite.
5. Commit: `ci: deploy generated font catalog to Pages`.

## Task 5: Documentation and real Release smoke test

**Files**
- Update `README.md`
- Update `DESIGN.md`
- Update `RELEASE_NOTES.md` if public catalog text is release-facing

**Steps**
1. Correct the obsolete 1-bit and old Font Maker repository statements.
2. Document Pages versus Release responsibilities, local build commands, and web schema.
3. Download the published `NotoSansSC_14.cpfont`, verify its manifest hash/size, parse it, and generate one PNG.
4. Run `python scripts/validate_config.py`, `python -m py_compile scripts/*.py`, `python -m unittest discover -s tests -v`, and `git diff --check`.
5. Commit: `docs: document public font catalog`.

## Task 6: Integration

1. Review branch diff and commits.
2. Push `feat/github-pages-font-catalog`.
3. Merge only after branch CI is green.
4. Enable GitHub Pages with Actions as its source if the repository has not yet been configured.
5. Manually dispatch `Deploy font catalog`, verify the public `catalog.json`, preview PNGs, HTML, and direct Release links.
