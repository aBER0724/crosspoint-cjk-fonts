# Contributing a font

[English](CONTRIBUTING.md) | [简体中文](CONTRIBUTING.zh-CN.md) | [日本語](CONTRIBUTING.ja.md)

Thanks for helping expand the CrossPoint Reader CJK font catalog. A font submission may include one uploaded TTF, OTF, or ZIP source file. The repository converts it into the seven physical `.cpfont v4` sizes after merge.

## Before you start

A submission must meet these technical requirements:

- The font covers Simplified Chinese, Traditional Chinese, or Japanese text.
- Upload the normal Regular/400 face. Variable fonts must declare the static axes used for the build.
- One pull request adds, updates, or removes one font family.
- The submitter must have permission to upload and redistribute the submitted file.

The catalog accepts proprietary fonts, personal-use-only fonts, non-commercial fonts, fonts with unclear terms, and files obtained from third-party download indexes. An original upstream repository and OFL license are not required.

The optional `license_type` field supports:

- `commercial-use` — **Commercial use allowed**;
- `personal-use` — **Personal use only**;
- omitted — **Unknown / not provided**.

This field is the submitter's declaration, not a repository verification or legal review. Include a `license_url` or note when available, but it may be omitted.

## 1. Fork and create a branch

Fork this repository on GitHub, clone your fork, and create one branch for one family:

```bash
git clone https://github.com/<your-name>/crosspoint-cjk-fonts.git
cd crosspoint-cjk-fonts
git switch -c font/<FamilyId>
```

`FamilyId` is the stable build ID and filename prefix. It must contain only ASCII letters, digits, `_`, or `-`, with at most 31 characters. Use a readable identifier such as `ZenMaruGothicJP`; do not use spaces or localized characters.

## 2. Upload the font file

Create a directory for the family and copy exactly one TTF, OTF, or ZIP source into it:

```text
community-fonts/<FamilyId>/
```

Example:

```text
community-fonts/ExampleSansJP/ExampleSans-Regular.ttf
```

A direct font file may use any clear filename. For ZIP sources, include only the needed package and set `archive_member` to the exact `.ttf` or `.otf` path inside it. Each uploaded file must stay below GitHub's 100 MiB repository file limit. Do not use Git LFS.

## 3. Add the catalog entry

Add one family to `config/fonts.yaml`. Do not change the catalog-wide size lists.

Uploaded TTF/OTF example:

```yaml
  - name: ExampleSansJP
    display_names: {en: "Example Sans", zh: "Example Sans", ja: "Example Sans"}
    description: "Short English description of coverage and style"
    category: sans-serif
    languages: [ja]
    license_type: commercial-use
    license_url: "https://example.com/license" # optional
    source_url: "https://example.com/download-page" # optional
    intervals: latin-ext,cjk
    source:
      path: community-fonts/ExampleSansJP/ExampleSans-Regular.ttf
```

Variable font example:

```yaml
    source:
      path: community-fonts/ExampleSansJP/ExampleSans-variable.ttf
      variable: {wght: 400}
```

ZIP example:

```yaml
    source:
      path: community-fonts/ExampleSansJP/example-fonts.zip
      archive_member: "fonts/ExampleSans-Regular.ttf"
```

Use only these current catalog values:

- `languages`: `zh-Hans`, `zh-Hant`, `ja` — include only languages the file actually covers.
- `category`: `sans-serif`, `serif`, `rounded-sans`, `handwriting`, `fangsong`, or `display`.
- `license_type`: optional `commercial-use` or `personal-use`.
- `intervals`: normally `latin-ext,cjk`.
- `force_autohint: true`: optional; use only when normal rasterization is visibly poor and explain it in the pull request.

`display_names` must contain non-empty `en`, `zh`, and `ja` values. Repeating the known font name is acceptable when no established localized name exists. These are reader-facing labels; `name` remains the stable ASCII ID.

Existing URL-based catalog entries may continue to use `url`, `filename`, and `sha256`. New community submissions should normally use `source.path` so the PR contains the exact font file to build.

## 4. Record the license declaration

Add one row to `LICENSES.md` containing:

- the stable family ID;
- the declared license type: Commercial use allowed, Personal use only, or Not provided;
- the download page, license link, author, copyright holder, or other attribution when known.

Do not describe an unknown license as verified. The repository displays the submitted declaration as-is.

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

Expected output is seven `.cpfont v4` files at 8, 10, 12, 14, 16, 18, and 22 pt. Do not add `dist/` or generated `.cpfont` files to Git.

If you cannot run FreeType locally, submit a draft PR after the configuration tests pass and say so in the checklist. A maintainer can trigger the single-family build.

## 6. Open the pull request

Push the branch and open a PR against `main`:

```bash
git add community-fonts/<FamilyId> config/fonts.yaml LICENSES.md
git commit -m "feat: add <font display name>"
git push -u origin font/<FamilyId>
```

The PR template asks for the uploaded file path, language coverage, optional license declaration, and validation results. Complete every applicable field. Keep the PR limited to one font family.

Pull requests from forks run read-only validation without Release credentials. Merging into `main` triggers the incremental Release workflow; unchanged families are reused, and only the submitted family is built and uploaded.

## Updating or removing a family

Use the same one-family PR rule. For an update, replace the uploaded source file and explain what changed. For removal, delete the `community-fonts/<FamilyId>/` directory, its `config/fonts.yaml` entry, and its `LICENSES.md` row. The Release workflow publishes the complete new manifest before cleaning obsolete assets.
