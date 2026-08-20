# CrossPoint CJK Fonts

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

本仓库提供 CrossPoint Reader 可选的 CJK `.cpfont` 字体。

## 提交字体

**请先阅读：[字体投稿指南](CONTRIBUTING.zh-CN.md)。**

简要流程：

1. Fork 本仓库，一个 PR 只处理一个字体家族。
2. 将一个 TTF、OTF 或 ZIP 文件放入 `community-fonts/<FamilyId>/`。
3. 在 [`config/fonts.yaml`](config/fonts.yaml) 中添加字体名称、覆盖语言、分类和文件路径。来源官网或源仓库地址可以选填。
4. 创建 Pull Request。GitHub 会自动填入检查表；也可以选择 **Font submission** 模板。

字段说明和完整示例见[字体投稿指南](CONTRIBUTING.zh-CN.md)。不要提交生成的 `.cpfont`、`dist/`、缓存、可执行文件或 Git LFS 对象。

## 字体目录

当前目录包含 16 个字体家族，覆盖简体中文、繁体中文和日文。Pages 会根据所选界面语言显示字体的原始名称或本地化名称，并在下方保留稳定 ASCII 构建 ID；搜索支持两种形式。每个家族都会按 [`config/fonts.yaml`](config/fonts.yaml) 中统一定义的七个字号生成：8/10/12 pt 用于 UI fallback，14/16/18/22 pt 用于阅读正文。

- 8/10/12 pt 提供 CJK UI fallback 字形。
- 14/16/18/22 pt 映射到阅读器的四个持久化字号档位；默认竖屏边距下，每行约可显示 16/14/12/10 个全角 CJK 字符。
- 固件只选择已安装的物理字体文件，不会在设备端缩放 CJK 字体。

每个字体家族已填写的来源地址见 [`SOURCES.md`](SOURCES.md)。

## 本地构建

要求：

- Python 3.11
- FreeType 开发库和运行时库

```bash
python -m pip install -r requirements.txt
python scripts/validate_config.py
python scripts/fetch_fallback.py
python scripts/build_fonts.py --clean
python scripts/verify_release.py dist
```

快速 smoke test：

```bash
python scripts/build_fonts.py --clean --only NotoSansSC
```

自行构建者可以只生成设备需要的字号，而不是完整目录契约：

```bash
python scripts/build_fonts.py --clean --only NotoSansSC --sizes 12,14,18,22
```

生成文件写入 `dist/`，并由 Git 忽略。

## 本地构建 Pages

Pages 生成器需要已发布的 manifest，以及每个家族的三个预览字号：

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

通过本地静态 HTTP 服务器打开 `site-dist/index.html`。生成的 `catalog.json` 使用 Web schema 1，并记录 `.cpfont` version 4 和 Release manifest version 2。

## GitHub Actions

- **Build font catalog**：在相关 Pull Request 和 `main` push 上验证配置、Python 代码、上传字体路径、`.cpfont v4` 解析器、预览渲染器、Pages 投影和工作流。手动运行可以选择一个家族（`smoke_family`），并可选地覆盖物理字号（`sizes`，逗号分隔）以构建自用目录。
- **Publish font release**：相关修改进入 `main` 后运行，只构建新增或变化的家族，复用未变化的已发布文件，验证完整资源清单，并更新固定的 `sd-fonts-m2-b4` Release。
- **Deploy font catalog**：字体 Release 成功后生成 14/18/22 pt PNG 预览，并部署 Pages 字体目录。

稳定设备端点：

```text
https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/fonts.json
https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/<Family>_<size>.cpfont
```

## 生成资源策略

上传的 TTF、OTF 和 ZIP 源文件应放在 `community-fonts/<FamilyId>/`。不要提交生成的 `.cpfont`、`dist/`、缓存、`fonts.json` 或 `site-dist/`。
