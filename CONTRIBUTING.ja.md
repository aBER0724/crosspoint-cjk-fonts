# フォントを投稿する

[English](CONTRIBUTING.md) | [简体中文](CONTRIBUTING.zh-CN.md) | [日本語](CONTRIBUTING.ja.md)

1つのフォント PR では、1つの CJK フォントファミリーだけを追加・更新・削除します。TTF、OTF、ZIP のいずれかを1つアップロードしてください。マージ後、GitHub Actions が7サイズの `.cpfont v4` を生成します。

## 投稿条件

- `zh-Hans`、`zh-Hant`、`ja` のいずれかを収録していること。
- 通常の Regular/400 を使用すること。Variable Font では、Regular を作るための軸値を指定してください。
- 1つの PR は1ファミリーに限定してください。
- ファイルは `community-fonts/<FamilyId>/` に置きます。Git LFS は使わないでください。
- 配布元サイトまたはソースリポジトリの URL は任意です。分からない場合は省略できます。

## 1. フォントファイルを追加する

ファミリー ID と同じ名前のディレクトリを作ります：

```text
community-fonts/<FamilyId>/
```

例：

```text
community-fonts/ExampleSansJP/ExampleSans-Regular.ttf
```

ファイル形式は TTF、OTF、ZIP に対応しています。サイズは 100 MiB 未満にしてください。ZIP を使う場合は、`archive_member` に実際に使う `.ttf` または `.otf` のパスを指定します。

`FamilyId` はビルド ID とファイル名の接頭辞になります。使用できる文字は ASCII 英数字、`_`、`-` で、最大31文字です。例：`ZenMaruGothicJP`。

## 2. カタログ設定を追加する

`config/fonts.yaml` に1件追加します。ファイル先頭の共通サイズ設定は変更しないでください。

```yaml
  - name: ExampleSansJP
    display_names: {en: "Example Sans"}
    # 任意：適切な名前や説明がある場合だけ zh、ja、description を追加します。
    category: sans-serif
    languages: [ja]
    source_url: "https://example.com/example-sans" # 任意
    intervals: latin-ext,cjk
    source:
      path: community-fonts/ExampleSansJP/ExampleSans-Regular.ttf
```

### 記入する項目

| Field | Required | Description |
| --- | --- | --- |
| `name` | 必須 | 安定した ASCII ファミリー ID。`community-fonts/<FamilyId>/` と一致させ、`.cpfont` のファイル名にも使います。 |
| `display_names.en` | 必須 | 英語表示名。別の英語名がなければ既知のフォント名をそのまま使えます。 |
| `display_names.zh` | 任意 | 中国語表示名。省略した場合、サイトは `display_names.en` を使います。 |
| `display_names.ja` | 任意 | 日本語表示名。省略した場合、サイトは `display_names.en` を使います。 |
| `description` | 任意 | スタイルや収録範囲を説明する短い英語文。不要なら省略できます。 |
| `category` | 必須 | `sans-serif`、`serif`、`rounded-sans`、`handwriting`、`fangsong`、`display` のいずれか。 |
| `languages` | 必須 | 実際に収録する言語。`zh-Hans`、`zh-Hant`、`ja` から選びます。複数指定できます。 |
| `source_url` | 任意 | フォント公式サイト、プロジェクトページ、またはソースリポジトリ。URL がなければ省略します。 |
| `intervals` | 必須 | 通常は `latin-ext,cjk`。 |
| `force_autohint` | 任意 | ビットマップ生成時の FreeType hint（ピクセル位置の調整）を制御します。省略または `false` ではフォント本来の hint を使います。小サイズで線の位置や太さが明らかに不揃いな場合は `true` にして、FreeType に hint を自動生成させます。 |
| `source.path` | アップロード時は必須 | `community-fonts/<FamilyId>/` 以下に置いた TTF、OTF、ZIP のパス。 |
| `source.archive_member` | ZIP の場合は必須 | ZIP 内で使用する `.ttf` または `.otf` の正確なパス。 |
| `source.variable` | Variable Font の場合は必須 | 静的インスタンスを作る軸値。例：`variable: {wght: 400}`。 |

Variable Font の例：

```yaml
    source:
      path: community-fonts/ExampleSansJP/ExampleSans-variable.ttf
      variable: {wght: 400}
```

ZIP の例：

```yaml
    source:
      path: community-fonts/ExampleSansJP/example-fonts.zip
      archive_member: "fonts/ExampleSans-Regular.ttf"
```

既存エントリでは `source.url`、`source.filename`、`source.sha256` を使っている場合があります。新規投稿では `source.path` を使ってください。

## 3. Pull Request を作成する

フォントファイルと設定をコミットします：

```bash
git add community-fonts/<FamilyId> config/fonts.yaml
git commit -m "feat: add <font display name>"
git push -u origin font/<FamilyId>
```

PR には、ファミリー ID、アップロードしたファイルのパス、収録言語、分類、任意の配布元 URL を記入してください。Variable Font や ZIP の場合は、軸値または `archive_member` も記入します。

Fork からの PR では、Release 権限を使わない読み取り専用チェックが走ります。マージ後は変更されたファミリーだけをビルドし、変更のないファイルは再利用します。

## 更新と削除

更新も1つの PR で1ファミリーだけを扱います。ファイルと `config/fonts.yaml` を更新し、変更点を書いてください。削除時は `community-fonts/<FamilyId>/` と対応する設定を削除します。
