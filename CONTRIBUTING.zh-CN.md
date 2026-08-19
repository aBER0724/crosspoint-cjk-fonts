# 提交字体

[English](CONTRIBUTING.md) | [简体中文](CONTRIBUTING.zh-CN.md) | [日本語](CONTRIBUTING.ja.md)

感谢你帮助扩充 CrossPoint Reader CJK 字体目录。字体投稿是一个**仅包含元数据的 Pull Request**：不要提交源字体或生成的 `.cpfont` 文件。PR 合并后，可信 Release 工作流会下载锁定的上游源文件，构建七个物理字号，完成验证，并原地更新固定 Release。

## 投稿前检查

提交的字体必须满足以下全部条件：

- 覆盖简体中文、繁体中文或日文。
- 本次提交的精确字体文件采用 **SIL Open Font License 1.1（OFL-1.1）**。
- 来源是原始项目或其他权威上游位置。
- 来源 URL 不可变：使用 Release tag 或完整 commit SHA，不要使用会变化的 `main`、`master` 或 `latest` URL。
- 记录源文件的 SHA-256。
- 提交 Regular/400 字重；可变字体必须声明构建时使用的静态 axes。
- 已检查 Reserved Font Name 和其他 OFL 命名条件。
- 一个 Pull Request 只新增、更新或删除一个字体家族。

不接受：

- 专有许可、仅限个人使用、禁止商业使用或许可不明确的字体。
- 从第三方下载索引复制、但无法提供权威上游来源的字体。
- 提交到仓库的源字体二进制、生成的 `.cpfont`、构建缓存、可执行文件或 Git LFS 对象。
- 包含无关字体家族或多个无关字重的打包文件。

如果不确定某个字体是否适合，请先创建 proposal issue 或 Draft PR，并附上上游和许可证链接，再准备完整投稿。

## 1. Fork 并创建分支

在 GitHub 上 Fork 本仓库，克隆你的 Fork，并为一个字体家族创建一个分支：

```bash
git clone https://github.com/<your-name>/crosspoint-cjk-fonts.git
cd crosspoint-cjk-fonts
git switch -c font/<FamilyId>
```

`FamilyId` 是稳定构建 ID 和文件名前缀。它只能包含 ASCII 字母、数字、`_` 或 `-`，最多 31 个字符。请使用类似 `ZenMaruGothicJP` 的可读标识，不要使用空格或本地化字符。

## 2. 锁定权威来源

找到原始上游仓库、其 OFL 文件，以及一个精确的 Regular 字体文件。优先使用带 tag 的 Release；否则固定到完整 commit SHA。

下载精确 URL，并计算 SHA-256：

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

如果来源是 ZIP，请计算 ZIP 文件本身的摘要，并通过 `archive_member` 指定 ZIP 内精确的 `.ttf` 或 `.otf` 路径。

## 3. 添加目录配置

在 `config/fonts.yaml` 中添加一个字体家族。不要修改全局字号列表。

静态 TTF/OTF 示例：

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

可变字体示例：

```yaml
    source:
      url: "https://raw.githubusercontent.com/owner/project/<full-commit>/fonts/ExampleSans%5Bwght%5D.ttf"
      filename: "ExampleSans-variable.ttf"
      sha256: "<64 lowercase hexadecimal characters>"
      variable: {wght: 400}
```

ZIP 示例：

```yaml
    source:
      url: "https://github.com/owner/project/releases/download/v1.0/example-fonts.zip"
      filename: "example-fonts-v1.0.zip"
      sha256: "<64 lowercase hexadecimal characters>"
      archive_member: "fonts/ExampleSans-Regular.ttf"
```

当前目录只允许以下值：

- `languages`：`zh-Hans`、`zh-Hant`、`ja`。只声明源文件实际覆盖的语言。
- `category`：`sans-serif`、`serif`、`rounded-sans`、`handwriting`、`fangsong` 或 `display`。
- `intervals`：通常使用 `latin-ext,cjk`。
- `force_autohint: true`：可选。仅当正常栅格化效果明显较差时使用，并在 PR 中说明视觉依据。

`display_names` 必须包含非空的 `en`、`zh` 和 `ja`。如果没有公认的本地化名称，可以重复官方名称。它们是面向用户的显示标签；`name` 始终是稳定 ASCII ID。

## 4. 记录许可证归属

在 `LICENSES.md` 中添加一行，包含：

- 稳定家族 ID；
- 固定的权威来源 URL；
- 固定的 OFL-1.1 URL；
- 与重新分发有关的 Reserved Font Name 或附加许可说明。

不要假设字体目录或镜像正确识别了许可证。请自行审阅上游许可证正文和版权信息。

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

预期生成 8、10、12、14、16、18 和 22 pt 七个 `.cpfont v4` 文件。**不要**将 `dist/`、下载的源文件或这些生成文件加入 Git。

如果无法在本地运行 FreeType，请在配置测试通过后提交 Draft PR，并在检查表中说明原因。维护者可以触发可信的单家族构建。

## 6. 创建 Pull Request

推送分支，并向 `main` 创建 PR：

```bash
git add config/fonts.yaml LICENSES.md
git commit -m "feat: add <font display name>"
git push -u origin font/<FamilyId>
```

PR 模板会要求填写上游来源、固定 revision、SHA-256、语言覆盖、许可证审核和验证结果。请完成所有适用字段，并确保 PR 只涉及一个字体家族。

Fork PR 会在没有 Release 凭据的情况下运行只读验证。维护者会审阅来源和许可证，并可能在合并前运行可信单家族转换。合并到 `main` 后会触发增量 Release 工作流：复用未变化的家族，只构建并上传本次提交的家族。

## 更新或删除字体家族

仍然遵守一个 PR 一个字体家族。更新时，固定新的来源 revision 和 SHA-256，并说明来源变化原因。删除时，说明许可证、质量、上游或兼容性原因，同时删除配置条目及其 `LICENSES.md` 行。Release 工作流会先发布新的完整 manifest，再清理废弃资源。
