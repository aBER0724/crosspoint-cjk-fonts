# Contributing a font

[English](CONTRIBUTING.md) | [简体中文](CONTRIBUTING.zh-CN.md) | [日本語](CONTRIBUTING.ja.md)

A font PR adds, updates, or removes one CJK font family. Upload one TTF, OTF, or ZIP file; after merge, GitHub Actions builds the seven `.cpfont v4` sizes.

## Before you start

- The font must cover `zh-Hans`, `zh-Hant`, or `ja`.
- Use the normal Regular/400 face. For a variable font, set the axes used to make that face.
- Keep the PR to one family.
- Put the file under `community-fonts/<FamilyId>/`. Do not use Git LFS.
- You may add the font's homepage or source repository. This link is optional.

## 1. Add the font file

Create a directory with the same name as the family ID:

```text
community-fonts/<FamilyId>/
```

For example:

```text
community-fonts/ExampleSansJP/ExampleSans-Regular.ttf
```

The file may be TTF, OTF, or ZIP and must be smaller than 100 MiB. A ZIP entry needs an `archive_member` pointing to the exact `.ttf` or `.otf` inside the archive.

`FamilyId` becomes the build ID and filename prefix. It may contain ASCII letters, digits, `_`, and `-`, up to 31 characters. `ZenMaruGothicJP` is a valid example.

## 2. Add the catalog entry

Add one item to `config/fonts.yaml`. Do not change the shared size lists.

```yaml
  - name: ExampleSansJP
    display_names: {en: "Example Sans"}
    # Optional: add zh/ja display names and a description when available.
    category: sans-serif
    languages: [ja]
    source_url: "https://example.com/example-sans" # optional
    intervals: latin-ext,cjk
    source:
      path: community-fonts/ExampleSansJP/ExampleSans-Regular.ttf
```

### Fields you enter

| Field | Required | Description |
| --- | --- | --- |
| `name` | Yes | Stable ASCII family ID. It must match `community-fonts/<FamilyId>/` and is used in `.cpfont` filenames. |
| `display_names.en` | Yes | English display name. Use the known font name if there is no separate English name. |
| `display_names.zh` | No | Chinese display name. If omitted, the site uses `display_names.en`. |
| `display_names.ja` | No | Japanese display name. If omitted, the site uses `display_names.en`. |
| `description` | No | Short English description of the font's style or coverage. Omit it if you do not need one. |
| `category` | Yes | One of `sans-serif`, `serif`, `rounded-sans`, `handwriting`, `fangsong`, or `display`. |
| `languages` | Yes | Any supported languages the file actually covers: `zh-Hans`, `zh-Hant`, `ja`. |
| `source_url` | No | Font homepage, project page, or source repository. Omit it if you do not have a link. |
| `intervals` | Yes | Selects the Unicode ranges rasterized into every `.cpfont`; it does not describe the font's language or style. For CJK submissions, use `latin-ext,cjk`: `latin-ext` adds Latin letters, numbers, and common punctuation, while `cjk` adds CJK punctuation, hiragana, katakana, common Han ideographs, compatibility ideographs, and full-width forms. The converter keeps only glyphs present in the submitted font or fallback and always adds U+FFFD. Presets may be comma-separated; advanced entries may add a range such as `(0x2100-0x214F)`. Adding ranges increases build time and file size. |
| `force_autohint` | No | Controls FreeType hinting during bitmap generation. Omit it or use `false` to keep the font's normal hinting; use `true` to make FreeType generate its own hints when small text has visibly uneven strokes or poor alignment. |
| `source.path` | Yes for uploads | Path to the uploaded TTF, OTF, or ZIP under `community-fonts/<FamilyId>/`. |
| `source.archive_member` | ZIP only | Exact `.ttf` or `.otf` path inside the ZIP. |
| `source.variable` | Variable fonts only | Static axes used for the build, for example `variable: {wght: 400}`. |

For a variable font:

```yaml
    source:
      path: community-fonts/ExampleSansJP/ExampleSans-variable.ttf
      variable: {wght: 400}
```

For a ZIP:

```yaml
    source:
      path: community-fonts/ExampleSansJP/example-fonts.zip
      archive_member: "fonts/ExampleSans-Regular.ttf"
```

Older entries may still use `source.url`, `source.filename`, and `source.sha256`. New PRs should use `source.path`.

## 3. Open the pull request

Commit the uploaded file and the catalog entry:

```bash
git add community-fonts/<FamilyId> config/fonts.yaml
git commit -m "feat: add <font display name>"
git push -u origin font/<FamilyId>
```

In the PR, include the family ID, uploaded file path, supported languages, category, and the optional source link. If the font is variable or packed in a ZIP, include the axes or archive member as well.

Pull requests from forks run read-only checks without Release credentials. After merge, the release workflow builds the changed family and reuses unchanged files.

## Updating or removing a family

An update also uses one PR for one family. Replace the uploaded file, update `config/fonts.yaml`, and note what changed. To remove a family, delete its `community-fonts/<FamilyId>/` directory and its config entry.
