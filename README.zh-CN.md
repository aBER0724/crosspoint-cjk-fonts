# CrossPoint CJK Fonts

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

本仓库为 CrossPoint Reader 的可选 CJK `.cpfont` 字体提供可复现构建和 GitHub Release 托管。

生成的二进制文件不会提交到 Git 历史。GitHub Actions 会下载经 SHA-256 锁定的上游字体源文件，将其转换为设备原生格式，生成 `fonts.json`，验证所有资源，并发布到 `sd-fonts-m2-b4` Release。

轻量浏览器字体目录发布于 GitHub Pages：

```text
https://aber0724.github.io/crosspoint-cjk-fonts/
```

Pages 仅包含 HTML、JSON 元数据，以及从真实 `.cpfont v4` 2-bit 位图解码得到的轻量 PNG 预览。所有字体下载仍直接指向版本化的 GitHub Release。

## 提交字体

**请先阅读：[字体投稿指南](CONTRIBUTING.zh-CN.md)。** 指南包括许可要求、完整的 `config/fonts.yaml` 示例、来源锁定与 SHA-256 说明、本地验证命令，以及维护者审核和发布流程。

简要流程：

1. Fork 本仓库，并为一个字体家族创建一个独立分支。
2. 选择权威上游提供的 **OFL-1.1** Regular/400 字体源，并固定到 Release tag 或完整 commit SHA。
3. 在 [`config/fonts.yaml`](config/fonts.yaml) 中增加一个条目，填写稳定 ASCII 家族 ID、本地化名称、实际语言覆盖、精确来源 URL 和 SHA-256。
4. 在 [`LICENSES.md`](LICENSES.md) 中增加固定的上游与许可证归属信息。
5. 运行配置测试；本地具备 FreeType 时，再执行单家族构建。
6. 创建 Pull Request。GitHub 会自动填入根检查表；在 `compare` → `New pull request` → `Get started` 中也可以选择专用的 **Font submission** 模板。

**不要**提交 TTF/OTF/ZIP 源文件或生成的 `.cpfont` 文件。PR 只包含目录配置和归属信息；可信工作流会在审核后下载锁定来源，并构建七个物理字号。一个 PR 只能新增、更新或删除一个字体家族。

## 字体目录

当前目录包含 16 个 OFL-1.1 字体家族，覆盖简体中文、繁体中文和日文。Pages 会根据所选界面语言显示字体的原始名称或本地化名称，并在下方保留稳定 ASCII 构建 ID；搜索支持两种形式。每个家族都会按 [`config/fonts.yaml`](config/fonts.yaml) 中统一定义的七个字号生成预览：8/10/12 pt 用于 UI fallback，14/16/18/22 pt 用于阅读正文。

- 8/10/12 pt 提供 CJK UI fallback 字形。
- 14/16/18/22 pt 映射到阅读器的四个持久化字号档位；默认竖屏边距下，每行约可显示 16/14/12/10 个全角 CJK 字符。
- 固件只选择已安装的物理字体文件，不会在设备端缩放 CJK 字体。

精确上游来源和归属信息见 [`LICENSES.md`](LICENSES.md)。

## 可复现性

来源 URL 和预期 SHA-256 位于 [`config/fonts.yaml`](config/fonts.yaml)。如果下载文件与锁定摘要不匹配，构建会在转换前停止。

用于补齐标点和基础 Latin 字形的 fallback 字体也由 [`scripts/fetch_fallback.py`](scripts/fetch_fallback.py) 使用 SHA-256 锁定。

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

- **Build font catalog**：在相关 Pull Request 和 `main` push 上验证配置、Python 代码、`.cpfont v4` 解析器、预览渲染器、Pages 投影和工作流。手动 smoke run 可以选择一个家族；可复用工作流接收 Release planner 选择的精确家族列表。
- **Publish font release**：相关修改进入 `main` 后自动运行；也可手动输入 `sd-fonts-m2-b4` 触发。工作流为每个家族计算影响二进制输出的指纹，复用固定 Release 中未变化的资源，只构建新增或变化的家族，验证完整资源清单，并在远程哈希验证通过后发布 `fonts.json`。`force_all` 可用于有意进行全量重建。Release Notes 根据前后 manifest 和构建计划生成，并使用 [`.github/RELEASE_TEMPLATE.md`](.github/RELEASE_TEMPLATE.md) 维护人类可读模板。
- **Deploy font catalog**：可手动运行，也会在字体 Release 成功或固定 Release 首次发布后运行。它只下载并验证 14/18/22 pt 文件，为每个已发布家族生成三张 PNG 预览，并部署不包含字体文件的 Pages artifact。

Release 包含 `build-index.json`，记录每个家族的可复现构建指纹和预期文件。首次增量运行从不可变的 `sd-fonts-m2-b4` tag 引导现有 Release；之后直接与已发布 index 比较。仅修改本地化名称等目录元数据不会重建字体；来源哈希、转换输入、物理字号、fallback 摘要、转换器代码或锁定的栅格化依赖发生变化时，相关输出会失效并重建。

稳定设备端点：

```text
https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/fonts.json
https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/<Family>_<size>.cpfont
```

公开仓库和 Release 是正式生产分发通道。本地开发时，固件测试覆盖配置也可指向局域网 HTTP 服务器中已经验证的 `release-assets/` 目录。

## 生成资源策略

不要提交 `.cpfont`、下载的源字体、缓存、`fonts.json` 或 `site-dist/`。Release assets 是二进制分发通道；Pages 是面向用户的字体目录和真实位图预览层，不是设备字体镜像或备用字体 CDN。
