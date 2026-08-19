# フォントを投稿する

[English](CONTRIBUTING.md) | [简体中文](CONTRIBUTING.zh-CN.md) | [日本語](CONTRIBUTING.ja.md)

CrossPoint Reader CJK フォントカタログへのご協力ありがとうございます。フォント投稿には、アップロードした TTF、OTF、ZIP ソースファイルを1つ含めることができます。マージ後、リポジトリが7つの物理サイズの `.cpfont v4` に変換します。

## 投稿前の確認

投稿は次の技術要件を満たす必要があります：

- 簡体字中国語、繁体字中国語、または日本語をカバーしていること。
- 通常の Regular/400 ウェイトをアップロードすること。Variable Font はビルドに使う静的 axes を宣言してください。
- 1つの Pull Request で追加・更新・削除するのは1つのフォントファミリーだけであること。
- 投稿者がファイルをアップロード・再配布する権限を持つこと。

プロプライエタリフォント、個人利用限定フォント、非商用フォント、ライセンスが不明確なフォント、第三者ダウンロード一覧から取得したファイルも受け付けます。元の上流リポジトリや OFL ライセンスは必須ではありません。

任意の `license_type` フィールドは次を使用できます：

- `commercial-use` — **商用利用可**。
- `personal-use` — **個人利用のみ**。
- 省略 — **不明 / 未提供**。

このフィールドは投稿者による申告であり、リポジトリによるライセンス確認や法的審査ではありません。`license_url`、作者情報、ダウンロードページが分かる場合は記入できますが、省略しても構いません。

## 1. Fork とブランチ作成

GitHub でこのリポジトリを Fork し、Fork を clone して、1つのフォントファミリー専用ブランチを作成します：

```bash
git clone https://github.com/<your-name>/crosspoint-cjk-fonts.git
cd crosspoint-cjk-fonts
git switch -c font/<FamilyId>
```

`FamilyId` は安定したビルド ID とファイル名プレフィックスです。ASCII の英字、数字、`_`、`-` のみを使用し、31文字以内にしてください。`ZenMaruGothicJP` のような読みやすい ID を使い、空白やローカライズ文字は使用しないでください。

## 2. フォントファイルをアップロードする

ファミリー用ディレクトリを作成し、TTF、OTF、ZIP ソースを1つ配置します：

```text
community-fonts/<FamilyId>/
```

例：

```text
community-fonts/ExampleSansJP/ExampleSans-Regular.ttf
```

直接フォントファイルには分かりやすい名前を付けてください。ZIP の場合は必要なパッケージだけをアップロードし、`archive_member` に ZIP 内の正確な `.ttf` または `.otf` パスを指定します。アップロードする各ファイルは GitHub リポジトリの 100 MiB 上限未満にしてください。Git LFS は使用しないでください。

## 3. カタログエントリを追加する

`config/fonts.yaml` に1つのファミリーを追加します。カタログ全体のサイズ一覧は変更しないでください。

アップロードした TTF/OTF の例：

```yaml
  - name: ExampleSansJP
    display_names: {en: "Example Sans", zh: "Example Sans", ja: "Example Sans"}
    description: "Short English description of coverage and style"
    category: sans-serif
    languages: [ja]
    license_type: commercial-use
    license_url: "https://example.com/license" # 任意
    source_url: "https://example.com/download-page" # 任意
    intervals: latin-ext,cjk
    source:
      path: community-fonts/ExampleSansJP/ExampleSans-Regular.ttf
```

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

現在使用できるカタログ値：

- `languages`：`zh-Hans`、`zh-Hant`、`ja`。ファイルが実際にカバーする言語だけを指定します。
- `category`：`sans-serif`、`serif`、`rounded-sans`、`handwriting`、`fangsong`、`display`。
- `license_type`：任意の `commercial-use` または `personal-use`。
- `intervals`：通常は `latin-ext,cjk`。
- `force_autohint: true`：任意。通常のラスタライズが明らかに悪い場合だけ使用し、PR で視覚的な理由を説明してください。

`display_names` には空でない `en`、`zh`、`ja` が必要です。定着したローカライズ名がない場合は、既知のフォント名を繰り返して構いません。これは利用者向け表示名であり、`name` は常に安定した ASCII ID です。

既存の URL ベースのカタログエントリは、引き続き `url`、`filename`、`sha256` を使用できます。新しいコミュニティ投稿では通常 `source.path` を使用し、ビルド対象の正確なフォントファイルを PR に含めてください。

## 4. ライセンス申告を記録する

`LICENSES.md` に1行を追加し、次を記録します：

- 安定したファミリー ID。
- 申告するライセンスタイプ：商用利用可、個人利用のみ、または未提供。
- 分かる場合はダウンロードページ、ライセンス URL、作者、著作権者、その他の帰属情報。

ライセンスが不明な場合は「確認済み」と書かないでください。カタログは投稿内容をそのまま表示します。

## 5. ローカルで検証する

設定だけの検証は短時間で完了します：

```bash
python -m pip install -r requirements.txt
python scripts/validate_config.py
python -m py_compile scripts/*.py
python -m unittest discover -s tests -v
```

単一ファミリーの完全ビルドには、FreeType の開発ライブラリとランタイムも必要です：

```bash
python scripts/fetch_fallback.py
python scripts/build_fonts.py --clean --only <FamilyId>
python scripts/verify_release.py dist
```

8、10、12、14、16、18、22 pt の7つの `.cpfont v4` が生成されることを確認します。`dist/` や生成済み `.cpfont` を Git に追加しないでください。

FreeType をローカルで実行できない場合は、設定テストが通った後に Draft PR を作成し、チェックリストに理由を書いてください。メンテナーが単一ファミリービルドを起動できます。

## 6. Pull Request を作成する

ブランチを push し、`main` 向けの PR を作成します：

```bash
git add community-fonts/<FamilyId> config/fonts.yaml LICENSES.md
git commit -m "feat: add <font display name>"
git push -u origin font/<FamilyId>
```

PR テンプレートには、アップロードしたファイルのパス、言語カバレッジ、任意のライセンス申告、検証結果を記入します。該当する項目をすべて埋め、PR を1つのフォントファミリーだけに限定してください。

Fork からの PR は Release 認証情報なしで読み取り専用検証を実行します。`main` へのマージ後、増分 Release ワークフローが起動し、変更のないファミリーを再利用して、投稿ファミリーだけをビルド・アップロードします。

## ファミリーの更新または削除

1つの PR で1つのファミリーという規則は同じです。更新ではアップロードしたソースファイルを置き換え、変更内容を説明してください。削除では `community-fonts/<FamilyId>/` ディレクトリ、`config/fonts.yaml` エントリ、`LICENSES.md` の行を削除してください。Release ワークフローは新しい完全 manifest を先に公開してから、古いアセットを削除します。
