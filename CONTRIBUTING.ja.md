# フォントを投稿する

[English](CONTRIBUTING.md) | [简体中文](CONTRIBUTING.zh-CN.md) | [日本語](CONTRIBUTING.ja.md)

CrossPoint Reader CJK フォントカタログへのご協力ありがとうございます。フォント投稿は、**メタデータだけを含む Pull Request** です。ソースフォントや生成済み `.cpfont` をコミットしないでください。PR のマージ後、信頼された Release ワークフローが固定済み上流ソースをダウンロードし、7つの物理サイズをビルド・検証して、固定 Release を更新します。

## 投稿前の確認

投稿するフォントは、次の条件をすべて満たす必要があります：

- 簡体字中国語、繁体字中国語、または日本語をカバーしていること。
- 投稿対象の正確なフォントファイルが **SIL Open Font License 1.1（OFL-1.1）** で提供されていること。
- ソースが元のプロジェクト、または他の信頼できる公式上流にあること。
- ソース URL が不変であること。Release tag または完全な commit SHA を使用し、変動する `main`、`master`、`latest` URL は使用しないでください。
- ソースファイルの SHA-256 を記録すること。
- Regular/400 ウェイトを投稿すること。Variable Font は、ビルドに使う静的 axes を宣言してください。
- Reserved Font Name およびその他の OFL 命名条件を確認していること。
- 1つの Pull Request で追加・更新・削除するのは1つのフォントファミリーだけであること。

受け付けないもの：

- プロプライエタリ、個人利用限定、非商用限定、またはライセンスが不明確なフォント。
- 公式上流を示せない第三者ダウンロード一覧から取得したフォント。
- リポジトリへコミットされたソースフォント、生成済み `.cpfont`、ビルドキャッシュ、実行ファイル、Git LFS オブジェクト。
- 無関係なフォントファミリーやウェイトを含むバンドル。

適合するか不明な場合は、完全な投稿を準備する前に、上流 URL とライセンス URL を添えて proposal issue または Draft PR を作成してください。

## 1. Fork とブランチ作成

GitHub でこのリポジトリを Fork し、Fork を clone して、1つのフォントファミリー専用ブランチを作成します：

```bash
git clone https://github.com/<your-name>/crosspoint-cjk-fonts.git
cd crosspoint-cjk-fonts
git switch -c font/<FamilyId>
```

`FamilyId` は安定したビルド ID とファイル名プレフィックスです。ASCII の英字、数字、`_`、`-` のみを使用し、31文字以内にしてください。`ZenMaruGothicJP` のような読みやすい ID を使い、空白やローカライズ文字は使用しないでください。

## 2. 公式ソースを固定する

元の上流リポジトリ、OFL ファイル、正確な Regular フォントファイルを確認します。tag 付き Release を優先し、存在しない場合は完全な commit SHA に固定してください。

正確な URL をダウンロードし、SHA-256 を計算します：

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

ZIP ソースの場合は ZIP 自体のハッシュを計算し、`archive_member` に ZIP 内の正確な `.ttf` または `.otf` パスを指定します。

## 3. カタログエントリを追加する

`config/fonts.yaml` に1つのファミリーを追加します。カタログ全体のサイズ一覧は変更しないでください。

静的 TTF/OTF の例：

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

Variable Font の例：

```yaml
    source:
      url: "https://raw.githubusercontent.com/owner/project/<full-commit>/fonts/ExampleSans%5Bwght%5D.ttf"
      filename: "ExampleSans-variable.ttf"
      sha256: "<64 lowercase hexadecimal characters>"
      variable: {wght: 400}
```

ZIP の例：

```yaml
    source:
      url: "https://github.com/owner/project/releases/download/v1.0/example-fonts.zip"
      filename: "example-fonts-v1.0.zip"
      sha256: "<64 lowercase hexadecimal characters>"
      archive_member: "fonts/ExampleSans-Regular.ttf"
```

現在使用できるカタログ値：

- `languages`：`zh-Hans`、`zh-Hant`、`ja`。ソースが実際にカバーする言語だけを指定します。
- `category`：`sans-serif`、`serif`、`rounded-sans`、`handwriting`、`fangsong`、`display`。
- `intervals`：通常は `latin-ext,cjk`。
- `force_autohint: true`：任意。通常のラスタライズが明らかに悪い場合だけ使用し、PR で視覚的な理由を説明してください。

`display_names` には空でない `en`、`zh`、`ja` が必要です。定着したローカライズ名がない場合は、公式名称を繰り返して構いません。これは利用者向け表示名であり、`name` は常に安定した ASCII ID です。

## 4. 帰属情報を記録する

`LICENSES.md` に1行を追加し、次を記録します：

- 安定したファミリー ID。
- 固定された公式ソース URL。
- 固定された OFL-1.1 URL。
- 再配布に関係する Reserved Font Name または追加許諾の注意点。

カタログやミラーのライセンス表示だけを信用しないでください。上流のライセンス本文と著作権情報を自分で確認してください。

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

8、10、12、14、16、18、22 pt の7つの `.cpfont v4` が生成されることを確認します。`dist/`、ダウンロードしたソース、生成ファイルを Git に**追加しないでください**。

FreeType をローカルで実行できない場合は、設定テストが通った後に Draft PR を作成し、チェックリストに理由を書いてください。メンテナーが信頼された単一ファミリービルドを起動できます。

## 6. Pull Request を作成する

ブランチを push し、`main` 向けの PR を作成します：

```bash
git add config/fonts.yaml LICENSES.md
git commit -m "feat: add <font display name>"
git push -u origin font/<FamilyId>
```

PR テンプレートには、上流ソース、固定 revision、SHA-256、言語カバレッジ、ライセンス確認、検証結果を記入します。該当する項目をすべて埋め、PR を1ファミリーだけに限定してください。

Fork からの PR は Release 認証情報なしで読み取り専用検証を実行します。メンテナーはソースとライセンスを確認し、マージ前に信頼された単一ファミリー変換を実行する場合があります。`main` へのマージ後、増分 Release ワークフローが起動し、変更のないファミリーを再利用して、投稿ファミリーだけをビルド・アップロードします。

## ファミリーの更新または削除

1つの PR で1つのファミリーという規則は同じです。更新では新しいソース revision と SHA-256 を固定し、変更理由を説明してください。削除ではライセンス、品質、上流、互換性上の理由を説明し、設定エントリと `LICENSES.md` の行を両方削除してください。Release ワークフローは新しい完全 manifest を先に公開してから、古いアセットを削除します。
