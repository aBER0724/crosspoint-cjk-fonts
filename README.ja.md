# CrossPoint CJK Fonts

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

CrossPoint Reader 向けのオプション CJK `.cpfont` フォントを提供するリポジトリです。

## フォントを投稿する

**最初に [フォント投稿ガイド](CONTRIBUTING.ja.md) をお読みください。**

概要：

1. リポジトリを Fork します。1つのフォント PR では1ファミリーだけを扱います。
2. TTF、OTF、ZIP のいずれかを `community-fonts/<FamilyId>/` に置きます。
3. [`config/fonts.yaml`](config/fonts.yaml) に名称、収録言語、分類、ファイルパスを追加します。配布元サイトまたはソースリポジトリの URL は任意です。
4. Pull Request を作成します。GitHub のチェックリスト、または **Font submission** テンプレートを使えます。

各フィールドの説明と設定例は[フォント投稿ガイド](CONTRIBUTING.ja.md)にあります。生成済み `.cpfont`、`dist/`、キャッシュ、実行ファイル、Git LFS オブジェクトはコミットしないでください。

## カタログ

現在のカタログには、簡体字中国語、繁体字中国語、日本語向けのフォントが16ファミリーあります。Pages は選択された UI 言語に応じて元の名称またはローカライズ名を表示し、その下に安定した ASCII ビルド ID を残します。検索はどちらの名称にも対応します。各ファミリーは [`config/fonts.yaml`](config/fonts.yaml) で一元管理される7サイズで生成されます。8/10/12 pt は UI fallback、14/16/18/22 pt は本文表示用です。

- 8/10/12 pt は CJK UI fallback グリフを提供します。
- 14/16/18/22 pt はリーダーの4つの保存済みサイズ枠に対応し、標準の縦向き余白では1行あたり約16/14/12/10文字の全角 CJK 文字を表示します。
- ファームウェアはインストール済みの物理ファイルを選択し、端末上で CJK フォントを拡大縮小しません。

各ファミリーの配布元 URL は [`SOURCES.md`](SOURCES.md) を参照してください。

## ローカルビルド

必要環境：

- Python 3.11
- FreeType の開発ライブラリおよびランタイム

```bash
python -m pip install -r requirements.txt
python scripts/validate_config.py
python scripts/fetch_fallback.py
python scripts/build_fonts.py --clean
python scripts/verify_release.py dist
```

簡単な smoke test：

```bash
python scripts/build_fonts.py --clean --only NotoSansSC
```

自前でビルドする方は、カタログ全体の契約ではなく、自分の端末に必要なサイズだけを生成できます：

```bash
python scripts/build_fonts.py --clean --only NotoSansSC --sizes 12,14,18,22
```

生成物は `dist/` に出力され、Git から除外されます。

## Pages のローカルビルド

Pages ジェネレーターには、公開済み manifest と、各ファミリーの3つのプレビューサイズだけが必要です：

```bash
mkdir -p release-assets .cache/pages-fonts
python -c "import urllib.request; urllib.request.urlretrieve('https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/fonts.json', 'release-assets/fonts.json')"
python scripts/fetch_release_previews.py \
  --manifest release-assets/fonts.json \
  --output .cache/pages-fonts \
  --sizes 14,18,22
python scripts/build_pages.py \
  --manifest release-assets/fonts.json \
  --fonts .cache/pages-fonts \
  --output site-dist
```

ローカル静的 HTTP サーバー経由で `site-dist/index.html` を開いてください。生成される `catalog.json` は Web schema 1 を使用し、`.cpfont` version 4 と Release manifest version 2 を記録します。

## GitHub Actions

- **Build font catalog**：関連する Pull Request と `main` push ごとに、設定、Python コード、アップロードされたフォントパス、`.cpfont v4` パーサー、プレビューレンダラー、Pages 投影、ワークフローを検証します。手動実行では1ファミリーを選択でき（`smoke_family`）、必要に応じて物理サイズを上書きできます（`sizes`、カンマ区切り）ので、自前カタログをビルドできます。
- **Publish font release**：関連変更が `main` に入ると実行され、新規または変更されたファミリーだけをビルドし、未変更の公開済みファイルを再利用します。完全なアセット一覧を検証し、固定の `sd-fonts-m2-b4` Release を更新します。
- **Deploy font catalog**：フォント Release の成功後に 14/18/22 pt の PNG プレビューを生成し、Pages カタログをデプロイします。

### 手動フォントビルド

Actions の UI からカスタムサイズのカタログをビルドする手順：

1. **Actions** タブを開き、**Build font catalog** ワークフローを選択します。
2. **Run workflow** をクリックします。
3. 下記の入力を設定し、再度 **Run workflow** をクリックします。

| 入力 | デフォルト | 効果 |
| --- | --- | --- |
| `smoke_family` | 空 | この1ファミリーだけを高速ビルドします。空なら全ファミリーをビルドします。 |
| `sizes` | 空 | 出力する物理サイズのカンマ区切りリスト（例: `12,14,18`）。空なら `config/fonts.yaml` の7サイズを使用します。 |

不正な `sizes`（空リスト、整数でない値、0 または負数）は、フォントをビルドする前に即座に失敗します。

端末向けの安定 URL：

```text
https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/fonts.json
https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/<Family>_<size>.cpfont
```

## 生成アセットの方針

アップロードする TTF、OTF、ZIP ソースは `community-fonts/<FamilyId>/` に配置します。生成済み `.cpfont`、`dist/`、キャッシュ、`fonts.json`、`site-dist/` はコミットしないでください。
