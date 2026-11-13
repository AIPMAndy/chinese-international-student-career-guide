# 构建、复现与首次发布

本文件记录本项目的构建边界和可重复执行步骤。版本：v1.0.0；核对日期：2026-11-13。所有命令均应在 `chinese-international-student-career-guide` 项目根目录执行。

公开网站已上线：<https://aipmandy.github.io/chinese-international-student-career-guide/>。GitHub 目标名称是 `AIPMAndy/chinese-international-student-career-guide`；该仓库尚未创建。实际发布状态和验证边界见[验证记录](verification.md)。

## 1. 文件来源与构建顺序

| 目录或文件 | 职责 |
| --- | --- |
| `content/core/` | 16个通用实操章节，Markdown 为正文源 |
| `content/regions/` | 20个境外国家或地区的独立正文 |
| `data/coverage-*.json` | 21条路线与20个缺口导航的真实状态；回国复用通用章 |
| `data/sources-*.json` | 官方来源、支持范围、核验日期和读取限制 |
| `templates/` | 已生成的 XLSX、CSV、Markdown 及使用说明 |
| `assets/fonts/` | PDF 所用字体子集及 OFL 许可 |
| `downloads/` | 完整 PDF、模板 ZIP、源代码 ZIP |
| `website/` | CSS、JavaScript、网站检查脚本与记录 |
| `dist/` | 可直接部署的静态成品，包括正文和下载 |

推荐顺序：修改并核验正文与来源 → 更新模板 → 生成 PDF → 完成模板包和源文件包 → 生成网站 → 验证 → 提交 → 发布。任何正文调整都应重新构建受影响载体，避免网站、PDF 与 Markdown 内容不一致。

本版“21条路线、20个缺口入口、90条来源”为实际内容计数。新增内容后应同时更新 README、版本记录和验证记录，不能只增加导航数字。

## 2. 网站：Python 标准库即可复现

需要 Python 3.10 或更新版本。构建器不联网，不需要 npm 或外部字体。

```bash
python3 scripts/build_site.py
python3 website/check_links.py
python3 -m http.server 8000 --directory dist
```

打开 `http://127.0.0.1:8000/`。构建器自动发现通用章、地区页、文字模板、覆盖登记和来源登记。正文写进 HTML，关闭 JavaScript 仍可阅读和打开链接；JavaScript 仅用于移动导航、筛选、复制微信号和打印。

正式发布到已经核实的域名时，设置 canonical 和 sitemap 的基址：

```bash
python3 scripts/build_site.py \
  --base-url https://aipmandy.github.io/chinese-international-student-career-guide
python3 website/check_links.py
```

确认新 GitHub 仓库确实存在后，才添加 `--repo-url` 参数并填入 API 或网页返回的真实仓库 URL。不要把计划名称先写成已发布链接。

`downloads/` 的文件会复制到 `dist/downloads/`，`templates/` 会复制到 `dist/templates/`。缺失文件不会出现假下载按钮。构建采用增量覆盖；删除或改名正文时，也应检查 `dist/` 中是否还有旧的生成页面，再重新验证。

## 3. PDF：字体、排版与逐页检查

安装文件中列出的依赖，再构建：

```bash
python3 -m pip install -r requirements-pdf.txt
python3 scripts/build_pdf.py
```

输出为 `downloads/chinese-international-student-career-guide.pdf`。本仓库包含本版所需的字体子集，可直接重建当前字符范围。新增字符时按[字体说明](../assets/fonts/README.md)从官方来源取得完整字体，并通过 `--font-source` 重新生成子集。

发布前检查 `docs/font-coverage.json`，并把 PDF 渲染为逐页图片检查封面、目录跳转、中文字体、分页、表格和截断。可以在安装了 Poppler 的环境中使用：

```bash
mkdir -p /tmp/student-career-pdf-review
pdftoppm -r 110 -png downloads/chinese-international-student-career-guide.pdf /tmp/student-career-pdf-review/page
```

逐页图像只是检查输入，不能用命令退出成功替代人工看图。核对页数、内链、外链和嵌入字体的实际结果，保存在 `docs/pdf-validation.json` 及最终发布验证记录中。

## 4. 工作簿与文本模板

读者直接使用 `templates/career-workbook.xlsx`，无需安装生成工具。CSV 和 Markdown 可由普通文本编辑器、Excel、WPS 或其他表格工具编辑；CSV 不保留公式、下拉和格式。

工作簿生成源为 `scripts/build_templates.mjs`，依赖本次制作环境的 `@oai/artifact-tool` 运行时。该运行时不被假定为普通公共 npm 依赖，因此本项目不提供未经验证的 `npm install` 承诺。具备该运行时、且 Node 模块解析能找到此包时，可执行：

```bash
node scripts/build_templates.mjs
```

生成器会重建 XLSX、8份 CSV、模板说明和 schema，运行12项公式边界检查，并把预览及公式检查输出到项目相邻的 `outputs/student-career-44af/`。模板正文的其他 Markdown 文件保留为可直接编辑源。修改生成器覆盖范围内的字段，应修改生成器后再生成，避免手工修改被下次运行覆盖。

没有该运行时仍可完整阅读、使用和编辑已交付工作簿、CSV、Markdown，并复现网站与 PDF。使用其他表格软件修改后，应检查公式、冻结、下拉与日期显示；不要把某一引擎的重算结果表述为所有软件兼容性保证。

## 5. ZIP 成品与发布前验收

模板包 `downloads/editable-templates.zip` 应包含 `templates/` 全部公开文件及适用的许可证。源文件包 `downloads/source-code.zip` 应包含正文、数据、模板、资产、构建脚本、样式、说明和许可；避免把 ZIP 自身再次打入 ZIP，也不包含 `.git`、本地凭据、会话配置、私人申请资料或临时浏览器下载。

使用随项目提供的脚本打包，再生成网站：

```bash
python3 scripts/validate_pdf.py --render
python3 scripts/package_release.py
python3 scripts/build_site.py --base-url https://aipmandy.github.io/chinese-international-student-career-guide
python3 website/check_links.py
```

打包脚本检查 ZIP CRC，并生成 `downloads/release-manifest.json` 中的 SHA256。源文件 ZIP 不包含生成的 `dist/`、`downloads/` 或站点身份配置，因此没有把自身递归打包；从该包解压后先构建 PDF，再打包和构建网站即可恢复成品。已导出的工作簿在 `templates/` 中可直接编辑。

打包完成后实际解压，检查 PDF、XLSX 与 Markdown 能打开，再重新生成网站，使下载按钮指向最终文件。源代码包应能按本文件步骤复现静态网站和当前 PDF。

最低验收记录：

- `website/static-validation.json`：全部本地文件链接、片段锚点、重复ID与主标题。
- `website/coverage-validation.json`：路线页、缺口入口和地区分组的真实计数。
- `website/mobile-validation.json`：390 / 375 CSS px 的实际窄视口操作及限制。
- `docs/template-validation.md`：公式、空白输入、下拉、结构与渲染范围。
- `docs/pdf-validation.json`：逐页渲染、字体、目录、页码与表格。
- 最终发布记录：真实仓库、站点与成品下载的访问结果；未完成事项按原样保留。

外部来源链接的可访问性和政策内容核验分开记录。登录墙、动态渲染限制或官方页面冲突应保留原状态，不能改写成“全部通过”。

## 6. GitHub 首次发布脚本

脚本位于 `scripts/publish-github.sh`。不带参数或传入 `--help` 只显示说明。脚本仅负责首次创建精确的新仓库，并推送已审阅的 `main` 与 `v1.0.0`；不会登录、切换账号、改写 `origin`、强推、删仓库或创建 Release。

先在当前新项目中准备提交。如果该目录已有 Sites Git 仓库，沿用它；不要再次初始化或改它的 `origin`。只有尚未初始化时才执行：

```bash
git init -b main
```

审阅公开文件并显式添加项目路径，避免把相邻目录或私人配置包含进来：

```bash
git add -- README.md LICENSE CONTENT_LICENSE.md CONTRIBUTING.md requirements-pdf.txt content data templates assets scripts website docs downloads dist .github
git diff --cached --stat
git diff --cached --check
git commit -m "Publish international student career guide v1.0.0"
```

如果已经有未完成修改或不是 `main`，先在本项目内完成审阅与分支安排。脚本不会替你丢弃修改、自动切换分支或批量提交。

已用 GitHub CLI 登录 AIPMAndy 后，先做只读检查：

```bash
bash scripts/publish-github.sh --check
```

检查包括：项目目录和 Git 根一致、项目身份文件、当前 `main`、工作区干净、成品存在且 ZIP 完整、版本标签没有指向别处、`gh auth status` 和 GitHub API 返回的登录账号均为 AIPMAndy。仅当精确目标仓库查询返回 HTTP 404，才认为可以尝试新建。403、超时和其他错误都会停止；若仓库已经存在，直接终止。

准备好公开发布时显式执行：

```bash
bash scripts/publish-github.sh --publish
```

发布行为限定于 `AIPMAndy/chinese-international-student-career-guide`：创建 public 仓库，新增专用 `github` remote，原子推送已检查的提交到 `main` 和 `v1.0.0`，读取远端 commit/tag 验证结果。GitHub 认证 helper 只应用于对应 Git 命令，不修改全局 Git 认证配置，也不改变原有分支的上游。

如果创建成功后推送失败，新仓库可能已经存在。脚本再次运行时会停止；应先检查这个新仓库的远端分支、标签与本地 `github` remote，再确定恢复动作。不要删除仓库、移走版本标签或改成覆盖既有仓库来绕过检查。首次脚本不是后续更新脚本。

## 7. 单独创建 Release 与上传成品

只有仓库、`main` 和 `v1.0.0` 已验证存在后，再创建 Release。先写准确的 `docs/release-notes-v1.0.0.md`，列出本版内容、覆盖深度、核验日期和真实限制；该文件由最终发布阶段提供。

以下命令只针对本项目，且 `--verify-tag` 要求远端标签已经存在：

```bash
gh release create v1.0.0 \
  downloads/chinese-international-student-career-guide.pdf \
  templates/career-workbook.xlsx \
  downloads/editable-templates.zip \
  downloads/source-code.zip \
  --repo AIPMAndy/chinese-international-student-career-guide \
  --verify-tag \
  --title "v1.0.0 中国留学生求职全局保姆级攻略" \
  --notes-file docs/release-notes-v1.0.0.md
```

创建后读取 Release，实际打开每个附件。已有同名 Release 或资产时先检查，不使用覆盖参数自动替换。

## 8. 可选 GitHub Pages

主要网站可以独立发布到 Sites；`origin` 保留其用途。GitHub Pages 是可选的另一静态部署目标，工作流位于 `.github/workflows/pages.yml`。

该工作流仅由 `workflow_dispatch` 手动触发，只接受本项目 `main`。它检查已提交的 `dist/` 并上传这个目录，不安装 npm，不改正文，不重新生成 PDF，也不触碰其他仓库。

要使用 Pages，在**本项目**的 Settings → Pages → Build and deployment 中选择 GitHub Actions，再到 Actions 手动运行工作流。实际地址以部署 job 输出的 `page_url` 为准，不预填未上线的 Pages 地址。工作流使用 `github-pages` 环境和部署所需的 `pages: write`、`id-token: write` 权限。

官方依据（2026-11-13 核对）：[自定义 GitHub Pages 工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)、[配置发布来源](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)、[GitHub CLI 新建仓库](https://cli.github.com/manual/gh_repo_create)、[GitHub CLI 新建 Release](https://cli.github.com/manual/gh_release_create)。如 GitHub 将来调整 action 版本，先对照官方说明再修改工作流。

## 作者

AI 酋长 Andy ｜ 微信：AIPMAndy ｜ 公众号：AI酋长Andy  
个人官网：<https://metaver.vip/> ｜ 公司官网：<https://www.a6no1.cn/>
