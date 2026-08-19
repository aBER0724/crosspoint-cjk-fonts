# Contributing a font

Thanks for helping expand the CrossPoint Reader CJK font catalog. A font submission is a **metadata-only pull request**: do not commit the source font or generated `.cpfont` files. The trusted Release workflow downloads the locked upstream source, builds seven physical sizes, verifies them, and updates the fixed Release after merge.

## Before you start

A submission must meet all of these requirements:

- The font covers Simplified Chinese, Traditional Chinese, or Japanese text.
- The exact submitted font is available under the **SIL Open Font License 1.1**.
- The source comes from the original project or another authoritative upstream location.
- The source URL is immutable: use a release tag or full commit SHA, not a moving `main`, `master`, or `latest` URL.
- The source file has a recorded SHA-256 digest.
- Submit the Regular/400 weight. Variable fonts must declare the static axes used for the build.
- Any Reserved Font Name or other OFL naming condition has been reviewed.
- One pull request adds or updates one font family.

Not accepted:

- Proprietary, personal-use-only, non-commercial, or unclear licenses.
- Fonts copied from third-party download indexes without an authoritative upstream source.
- Source font binaries, generated `.cpfont` files, build caches, executable files, or Git LFS objects committed to the repository.
- Bundles containing unrelated font families or weights.

If you are unsure whether a font is suitable, open a proposal issue or draft pull request with the upstream and license links before doing the full submission.

## 1. Fork and create a branch

Fork this repository on GitHub, clone your fork, and create one branch for one family:

```bash
git clone https://github.com/<your-name>/crosspoint-cjk-fonts.git
cd crosspoint-cjk-fonts
git switch -c font/<FamilyId>
```

`FamilyId` is the stable build ID and filename prefix. It must contain only ASCII letters, digits, `_`, or `-`, with at most 31 characters. Use a readable identifier such as `ZenMaruGothicJP`; do not use spaces or localized characters.

## 2. Pin the authoritative source

Locate the original upstream repository, its OFL file, and one exact Regular font file. Prefer a tagged release; otherwise pin a full commit SHA.

Download the exact URL and calculate its SHA-256:

```bash
python - <<'PY'
import hashlib
from pathlib import Path

path = Path("/path/to/Font-Regular.ttf")
digest = hashlib.sha256()
with path.open("rb") as source:
    for chunk in iter(lambda: source.read(1024 * 1024), b""):
        digest.update(chunk)
print(digest.hexdigest())
PY
```

For a ZIP source, hash the ZIP itself and set `archive_member` to the exact `.ttf` or `.otf` path inside it.

## 3. Add the catalog entry

Add one family to `config/fonts.yaml`. Do not change the catalog-wide size lists.

Static TTF/OTF example:

```yaml
  - name: ExampleSansJP
    display_names: {en: "Example Sans", zh: "Example Sans", ja: "Example Sans"}
    description: "Short English description of coverage and style"
    category: sans-serif
    languages: [ja]
    license: OFL-1.1
    license_url: "https://github.com/owner/project/blob/<tag-or-commit>/OFL.txt"
    source_url: "https://github.com/owner/project/tree/<tag-or-commit>"
    intervals: latin-ext,cjk
    source:
      url: "https://raw.githubusercontent.com/owner/project/<full-commit>/fonts/ExampleSans-Regular.ttf"
      filename: "ExampleSans-Regular.ttf"
      sha256: "<64 lowercase hexadecimal characters>"
```

Variable font example:

```yaml
    source:
      url: "https://raw.githubusercontent.com/owner/project/<full-commit>/fonts/ExampleSans%5Bwght%5D.ttf"
      filename: "ExampleSans-variable.ttf"
      sha256: "<64 lowercase hexadecimal characters>"
      variable: {wght: 400}
```

ZIP example:

```yaml
    source:
      url: "https://github.com/owner/project/releases/download/v1.0/example-fonts.zip"
      filename: "example-fonts-v1.0.zip"
      sha256: "<64 lowercase hexadecimal characters>"
      archive_member: "fonts/ExampleSans-Regular.ttf"
```

Use only these current catalog values:

- `languages`: `zh-Hans`, `zh-Hant`, `ja` — include only languages the source actually covers.
- `category`: `sans-serif`, `serif`, `rounded-sans`, `handwriting`, `fangsong`, or `display`.
- `intervals`: normally `latin-ext,cjk`.
- `force_autohint: true`: optional; use only when normal rasterization is visibly poor and explain it in the pull request.

`display_names` must contain non-empty `en`, `zh`, and `ja` values. Repeating the official name is acceptable when no established localized name exists. These are reader-facing labels; `name` remains the stable ASCII ID.

## 4. Record attribution

Add one row to `LICENSES.md` containing:

- the stable family ID;
- the pinned authoritative source URL;
- the pinned OFL-1.1 URL;
- any Reserved Font Name or additional-permission consideration relevant to redistribution.

Do not assume that a catalog or mirror has correctly identified the license. Review the upstream license text and copyright information yourself.

## 5. Validate locally

Configuration-only validation is quick:

```bash
python -m pip install -r requirements.txt
python scripts/validate_config.py
python -m py_compile scripts/*.py
python -m unittest discover -s tests -v
```

A full single-family build additionally requires FreeType development/runtime libraries:

```bash
python scripts/fetch_fallback.py
python scripts/build_fonts.py --clean --only <FamilyId>
python scripts/verify_release.py dist
```

Expected output is seven `.cpfont v4` files at 8, 10, 12, 14, 16, 18, and 22 pt. Do **not** add `dist/`, downloaded sources, or those generated files to Git.

If you cannot run FreeType locally, submit a draft PR after the configuration tests pass and say so in the checklist. A maintainer can trigger the trusted single-family build.

## 6. Open the pull request

Push the branch and open a PR against `main`:

```bash
git add config/fonts.yaml LICENSES.md
git commit -m "feat: add <font display name>"
git push -u origin font/<FamilyId>
```

The PR template asks for the upstream source, pinned revision, SHA-256, language coverage, license review, and validation results. Complete every applicable field. Keep the PR limited to one family.

Pull requests from forks run read-only validation without Release credentials. Maintainers review the source and license and may run a trusted single-family conversion before merge. Merging into `main` triggers the incremental Release workflow; unchanged families are reused, and only the submitted family is built and uploaded.

## Updating or removing a family

Use the same one-family PR rule. For an update, pin the new source revision and SHA-256 and explain why the source changed. For removal, explain the licensing, quality, upstream, or compatibility reason and remove both the configuration entry and its `LICENSES.md` row. The Release workflow publishes the complete new manifest before cleaning obsolete assets.
