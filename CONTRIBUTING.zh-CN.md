# 提交字体

[English](CONTRIBUTING.md) | [简体中文](CONTRIBUTING.zh-CN.md) | [日本語](CONTRIBUTING.ja.md)

一个字体 PR 只处理一个 CJK 字体家族。你只要上传一个 TTF、OTF 或 ZIP 文件；合并后，GitHub Actions 会生成七个字号的 `.cpfont v4`。

## 投稿要求

- 字体至少覆盖 `zh-Hans`、`zh-Hant` 或 `ja` 中的一种。
- 使用 Regular/400 字重。可变字体需要写明生成 Regular 字重所用的轴值。
- 一个 PR 只新增、更新或删除一个家族。
- 字体文件放在 `community-fonts/<FamilyId>/`，不要使用 Git LFS。
- 可以提供字体的来源官网或源仓库地址。没有地址时可不填。

## 1. 上传字体文件

新建一个与家族 ID 同名的目录：

```text
community-fonts/<FamilyId>/
```

例如：

```text
community-fonts/ExampleSansJP/ExampleSans-Regular.ttf
```

文件可以是 TTF、OTF 或 ZIP，大小必须低于 100 MiB。上传 ZIP 时，还要用 `archive_member` 写明 ZIP 内实际使用的 `.ttf` 或 `.otf` 路径。

`FamilyId` 会成为构建 ID 和文件名前缀。它最多 31 个字符，只能使用 ASCII 字母、数字、`_` 和 `-`。例如 `ZenMaruGothicJP`。

## 2. 添加目录配置

在 `config/fonts.yaml` 中增加一个条目，不要修改顶部的公共字号列表。

```yaml
  - name: ExampleSansJP
    display_names: {en: "Example Sans", zh: "Example Sans", ja: "Example Sans"}
    description: "Japanese sans-serif with kana and kanji"
    category: sans-serif
    languages: [ja]
    source_url: "https://example.com/example-sans" # 可选
    intervals: latin-ext,cjk
    source:
      path: community-fonts/ExampleSansJP/ExampleSans-Regular.ttf
```

### 需要填写的参数

| 字段 | 是否必填 | 简要说明 |
| --- | --- | --- |
| `name` | 是 | 稳定的 ASCII 家族 ID。必须与 `community-fonts/<FamilyId>/` 一致，也会用于 `.cpfont` 文件名。 |
| `display_names.en` | 是 | 英文显示名。没有单独英文名时，重复字体原名即可。 |
| `display_names.zh` | 是 | 中文显示名。没有通用中文名时，重复字体原名即可。 |
| `display_names.ja` | 是 | 日文显示名。没有通用日文名时，重复字体原名即可。 |
| `description` | 是 | 简短的英文说明，写清字体风格和大致覆盖范围即可。 |
| `category` | 是 | 可选值：`sans-serif`、`serif`、`rounded-sans`、`handwriting`、`fangsong`、`display`。 |
| `languages` | 是 | 字体实际覆盖的语言，可选 `zh-Hans`、`zh-Hant`、`ja`。可以填写多个。 |
| `source_url` | 否 | 字体来源官网、项目页或源仓库地址。没有可靠地址时直接省略。 |
| `intervals` | 是 | 通常填写 `latin-ext,cjk`。 |
| `force_autohint` | 否 | 只有正常渲染明显不佳时才设为 `true`，并在 PR 中说明原因。 |
| `source.path` | 上传文件时必填 | TTF、OTF 或 ZIP 在仓库中的路径，必须位于 `community-fonts/<FamilyId>/`。 |
| `source.archive_member` | ZIP 必填 | ZIP 内实际使用的 `.ttf` 或 `.otf` 路径。 |
| `source.variable` | 可变字体必填 | 构建静态字重所用的轴值，例如 `variable: {wght: 400}`。 |

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

旧条目可能仍使用 `source.url`、`source.filename` 和 `source.sha256`。新投稿统一使用 `source.path`。

## 3. 创建 Pull Request

提交字体文件和目录配置：

```bash
git add community-fonts/<FamilyId> config/fonts.yaml
git commit -m "feat: add <font display name>"
git push -u origin font/<FamilyId>
```

PR 中写明家族 ID、上传文件路径、覆盖语言、分类和可选的来源地址。如果是可变字体或 ZIP，再补充轴值或 `archive_member`。

Fork PR 会运行不带 Release 凭据的只读检查。合并后，发布工作流只构建发生变化的家族，未变化的字体会直接复用。

## 更新或删除字体

更新字体时仍然一个 PR 处理一个家族：替换文件、更新 `config/fonts.yaml`，并说明改了什么。删除字体时，删除 `community-fonts/<FamilyId>/` 目录和对应的配置条目。
