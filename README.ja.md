# CrossPoint CJK Fonts

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

CrossPoint Reader 向けのオプション CJK `.cpfont` フォントを、再現可能な方法でビルドし、GitHub Release から配布するリポジトリです。

生成済みバイナリは Git 履歴へコミットしません。GitHub Actions が SHA-256 で固定された上流フォントをダウンロードし、端末ネイティブ形式へ変換して `fonts.json` を生成し、すべてのアセットを検証したうえで `sd-fonts-m2-b4` Release に公開します。

軽量なブラウザ用フォントカタログは GitHub Pages で公開しています：

```text
https://aber0724.github.io/crosspoint-cjk-fonts/
```

Pages に含まれるのは HTML、JSON メタデータ、および実際の `.cpfont v4` 2-bit ビットマップからデコードした小さな PNG プレビューだけです。フォントのダウンロード先は、引き続きバージョン管理された GitHub Release です。

## フォントを投稿する

**最初に [フォント投稿ガイド](CONTRIBUTING.ja.md) をお読みください。** 受け入れ可能なライセンス、完全な `config/fonts.yaml` の例、取得元の固定方法、SHA-256、ローカル検証コマンド、メンテナーによるレビューと公開手順を説明しています。

概要：

1. リポジトリを Fork し、1つのフォントファミリー専用のブランチを作成します。
2. 信頼できる公式上流から、**OFL-1.1** の Regular/400 フォントを選び、Release tag または完全な commit SHA に固定します。
3. [`config/fonts.yaml`](config/fonts.yaml) に、安定した ASCII ファミリー ID、ローカライズ名、実際の言語カバレッジ、正確な取得 URL、SHA-256 を持つ1件のエントリを追加します。
4. [`LICENSES.md`](LICENSES.md) に、固定された上流 URL とライセンス帰属を追加します。
5. 設定テストを実行し、FreeType を利用できる場合は単一ファミリーのビルドも実行します。
6. Pull Request を作成します。GitHub はルートのチェックリストを自動挿入します。また、`compare` → `New pull request` → `Get started` から専用の **Font submission** テンプレートも選択できます。

TTF/OTF/ZIP ソースや生成済み `.cpfont` を**コミットしないでください**。PR に含めるのはカタログ設定と帰属情報だけです。レビュー後、信頼されたワークフローが固定済みソースを取得し、7つの物理サイズをビルドします。1つの PR で追加・更新・削除できるのは1つのフォントファミリーだけです。

## カタログ

現在のカタログには、簡体字中国語、繁体字中国語、日本語向けの OFL-1.1 フォントが16ファミリーあります。Pages は選択された UI 言語に応じて元の名称またはローカライズ名を表示し、その下に安定した ASCII ビルド ID を残します。検索はどちらの名称にも対応します。各ファミリーは [`config/fonts.yaml`](config/fonts.yaml) で一元管理される7サイズでプレビューされます。8/10/12 pt は UI fallback、14/16/18/22 pt は本文表示用です。

- 8/10/12 pt は CJK UI fallback グリフを提供します。
- 14/16/18/22 pt はリーダーの4つの保存済みサイズ枠に対応し、標準の縦向き余白では1行あたり約16/14/12/10文字の全角 CJK 文字を表示します。
- ファームウェアはインストール済みの物理ファイルを選択し、端末上で CJK フォントを拡大縮小しません。

正確な上流 URL と帰属情報は [`LICENSES.md`](LICENSES.md) を参照してください。

## 再現性

取得 URL と期待される SHA-256 は [`config/fonts.yaml`](config/fonts.yaml) に記録されています。ダウンロードしたソースが固定済みダイジェストと一致しない場合、変換前にビルドを停止します。

句読点と基本 Latin グリフを補う fallback フォントも、[`scripts/fetch_fallback.py`](scripts/fetch_fallback.py) によって SHA-256 で固定されています。

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

- **Build font catalog**：関連する Pull Request と `main` push ごとに、設定、Python コード、`.cpfont v4` パーサー、プレビューレンダラー、Pages 投影、ワークフローを検証します。手動 smoke run では1ファミリーを選択でき、再利用可能ワークフローは Release planner が選んだ正確なファミリー一覧を受け取ります。
- **Publish font release**：関連変更が `main` に入ると自動実行されます。`sd-fonts-m2-b4` を入力して手動実行することもできます。各ファミリーのバイト出力に関係する入力を fingerprint 化し、固定 Release にある未変更アセットを再利用し、新規または変更されたファミリーだけをビルドします。完全なアセット一覧を検証し、変更済みバイナリのリモートハッシュ検証後に `fonts.json` を公開します。意図的な全件再ビルドには `force_all` を使用できます。Release Notes は変更前後の manifest と build plan から生成され、[`.github/RELEASE_TEMPLATE.md`](.github/RELEASE_TEMPLATE.md) が人間向けテンプレートです。
- **Deploy font catalog**：手動、フォント Release の成功後、または固定 Release の初回公開後に実行されます。14/18/22 pt のみをダウンロード・検証し、公開済みファミリーごとに3枚の PNG プレビューを生成して、フォントを含まない Pages artifact をデプロイします。

Release には `build-index.json` が含まれ、各ファミリーの再現可能な build fingerprint と期待ファイルを記録します。最初の増分実行は不変の `sd-fonts-m2-b4` tag から既存 Release を初期化し、以降は公開済み index と直接比較します。ローカライズ名などカタログ専用メタデータの変更ではバイナリを再ビルドしません。ソースハッシュ、変換入力、物理サイズ、fallback ダイジェスト、変換コード、固定済みラスタライズ依存関係が変わると、該当出力を再ビルドします。

端末向けの安定 URL：

```text
https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/fonts.json
https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/<Family>_<size>.cpfont
```

公開リポジトリと Release が本番配布チャネルです。ローカル開発では、ファームウェアのテスト用上書き設定を、検証済み `release-assets/` ディレクトリを配信する LAN HTTP サーバーに向けることもできます。

## 生成アセットの方針

`.cpfont`、ダウンロード済みソースフォント、キャッシュ、`fonts.json`、`site-dist/` をコミットしないでください。Release assets がバイナリ配布チャネルです。Pages は人が閲覧するカタログと実ビットマップのプレビュー層であり、端末フォントのミラーや代替 CDN ではありません。
