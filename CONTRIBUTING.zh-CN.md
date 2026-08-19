# 提交字体

[English](CONTRIBUTING.md) | [简体中文](CONTRIBUTING.zh-CN.md) | [日本語](CONTRIBUTING.ja.md)

感谢你帮助扩充 CrossPoint Reader CJK 字体目录。字体投稿可以包含一个上传的 TTF、OTF 或 ZIP 源文件。合并后，仓库会将其转换为七个物理字号的 `.cpfont v4`。

## 投稿前检查

提交必须满足以下技术要求：

- 覆盖简体中文、繁体中文或日文。
- 上传正常 Regular/400 字重；可变字体必须声明构建时使用的静态 axes。
- 一个 Pull Request 只新增、更新或删除一个字体家族。
- 投稿者应确认自己有权上传和重新分发该文件。

目录允许专有字体、仅限个人使用的字体、禁止商业使用的字体、许可不明确的字体，以及从第三方下载索引获得的文件。不要求原始上游仓库，也不要求 OFL 许可。

可选的 `license_type` 字段支持：

- `commercial-use` — **免费商用**；
- `personal-use` — **个人使用** / 仅限个人使用；
- 不填写 — **未知 / 未提供**。

该字段只是投稿者声明，不代表仓库已经核验许可证或提供法律审核。若有 `license_url`、作者说明或下载页，可以填写；没有时可以不填。

## 1. Fork 并创建分支

在 GitHub 上 Fork 本仓库，克隆你的 Fork，并为一个字体家族创建一个分支：

```bash
git clone https://github.com/<your-name>/crosspoint-cjk-fonts.git
cd crosspoint-cjk-fonts
git switch -c font/<FamilyId>
```

`FamilyId` 是稳定构建 ID 和文件名前缀。它只能包含 ASCII 字母、数字、`_` 或 `-`，最多 31 个字符。请使用类似 `ZenMaruGothicJP` 的可读标识，不要使用空格或本地化字符。

## 2. 上传字体文件

创建家族目录，并放入一个 TTF、OTF 或 ZIP 源文件：

```text
community-fonts/<FamilyId>/
```

示例：

```text
community-fonts/ExampleSansJP/ExampleSans-Regular.ttf
```

直接字体文件可以使用清晰的文件名。如果来源是 ZIP，请只上传需要的包，并通过 `archive_member` 指定 ZIP 内精确的 `.ttf` 或 `.otf` 路径。单个上传文件必须小于 GitHub 仓库的 100 MiB 文件上限。不要使用 Git LFS。

## 3. 添加目录配置

在 `config/fonts.yaml` 中添加一个字体家族。不要修改全局字号列表。

上传 TTF/OTF 示例：

```yaml
  - name: ExampleSansJP
    display_names: {en: "Example Sans", zh: "Example Sans", ja: "Example Sans"}
    description: "Short English description of coverage and style"
    category: sans-serif
    languages: [ja]
    license_type: commercial-use
    license_url: "https://example.com/license" # 可选
    source_url: "https://example.com/download-page" # 可选
    intervals: latin-ext,cjk
    source:
      path: community-fonts/ExampleSansJP/ExampleSans-Regular.ttf
```

可变字体示例：

```yaml
    source:
      path: community-fonts/ExampleSansJP/ExampleSans-variable.ttf
      variable: {wght: 400}
```

ZIP 示例：

```yaml
    source:
      path: community-fonts/ExampleSansJP/example-fonts.zip
      archive_member: "fonts/ExampleSans-Regular.ttf"
```

当前目录只允许以下值：

- `languages`：`zh-Hans`、`zh-Hant`、`ja`。只声明文件实际覆盖的语言。
- `category`：`sans-serif`、`serif`、`rounded-sans`、`handwriting`、`fangsong` 或 `display`。
- `license_type`：可选的 `commercial-use` 或 `personal-use`。
- `intervals`：通常使用 `latin-ext,cjk`。
- `force_autohint: true`：可选。仅当正常栅格化效果明显较差时使用，并在 PR 中说明视觉依据。

`display_names` 必须包含非空的 `en`、`zh` 和 `ja`。如果没有公认的本地化名称，可以重复已知字体名称。它们是面向用户的显示标签；`name` 始终是稳定 ASCII ID。

现有 URL 方式的目录条目可以继续使用 `url`、`filename` 和 `sha256`。新的社区投稿通常应使用 `source.path`，使 PR 本身包含构建所需的精确字体文件。

## 4. 记录许可声明

在 `LICENSES.md` 中添加一行，包含：

- 稳定家族 ID；
- 声明的许可类型：免费商用、仅限个人使用或未提供；
- 已知的下载页、许可证链接、作者、版权所有者或其他归属信息。

许可未知时不要写成“已核验”。目录会按投稿者填写内容展示。

## 5. 本地验证

仅配置验证速度较快：

```bash
python -m pip install -r requirements.txt
python scripts/validate_config.py
python -m py_compile scripts/*.py
python -m unittest discover -s tests -v
```

完整单家族构建还需要 FreeType 开发库和运行时库：

```bash
python scripts/fetch_fallback.py
python scripts/build_fonts.py --clean --only <FamilyId>
python scripts/verify_release.py dist
```

预期生成 8、10、12、14、16、18 和 22 pt 七个 `.cpfont v4` 文件。不要将 `dist/` 或生成的 `.cpfont` 文件加入 Git。

如果无法在本地运行 FreeType，请在配置测试通过后提交 Draft PR，并在检查表中说明原因。维护者可以触发单家族构建。

## 6. 创建 Pull Request

推送分支，并向 `main` 创建 PR：

```bash
git add community-fonts/<FamilyId> config/fonts.yaml LICENSES.md
git commit -m "feat: add <font display name>"
git push -u origin font/<FamilyId>
```

PR 模板会要求填写上传文件路径、语言覆盖、可选的许可声明和验证结果。请完成所有适用字段，并确保 PR 只涉及一个字体家族。

Fork PR 会在没有 Release 凭据的情况下运行只读验证。合并到 `main` 后会触发增量 Release 工作流：复用未变化的家族，只构建并上传本次提交的家族。

## 更新或删除字体家族

仍然遵守一个 PR 一个字体家族。更新时，替换上传的源文件并说明变化。删除时，同时删除 `community-fonts/<FamilyId>/` 目录、`config/fonts.yaml` 条目和 `LICENSES.md` 行。Release 工作流会先发布新的完整 manifest，再清理废弃资源。
