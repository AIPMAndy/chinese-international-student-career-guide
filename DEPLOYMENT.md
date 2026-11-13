# GitHub Pages 发布

项目：中国留学生求职全局保姆级攻略。本要求更新于 **2026-11-13**，对应用户明确的部署纠正。

## 唯一正式部署目标

- GitHub 目标仓库：`AIPMAndy/chinese-international-student-career-guide`。
- 默认分支：`main`。
- 站点成品：GitHub Actions 在每次发布时从 `content/`、`data/`、`templates/`、`website/` 和 `scripts/build_site.py` 重建 `dist/`；仓库内 `dist/` 为历史构建快照，不能代替实际运行产物。
- 发布工作流：`.github/workflows/pages.yml`。
- 正式 Pages 地址：[https://aipmandy.github.io/chinese-international-student-career-guide/](https://aipmandy.github.io/chinese-international-student-career-guide/)。已从成功部署日志确认。

## 已完成的发布验收

公开仓库、`main` 与成品已经可读。[工作流 43487144595](https://github.com/AIPMAndy/chinese-international-student-career-guide/actions/runs/43487144595) 对应提交 `0d22d503acc99760e3950172946dab471c0521ba`，部署及 8 项发布后 HTTP / SHA-256 检查全部成功，覆盖首页、正文、CSS、JS、PDF、XLSX、模板 ZIP 和源码 ZIP。该记录绑定此提交，后续更新应取得新的工作流结果。

ChatGPT Pages / Sites 不再作为此项目的正式部署目标。保留的历史配置不能作为继续发布到旧服务的依据。

## 发布前

1. 在本项目完成内容、移动端排版、PDF、模板和下载包验收。已有正文和设计继续复用。
2. 构建顺序为源文件 → `scripts/package_release.py`（重打 ZIP）→ `scripts/build_site.py --base-url https://aipmandy.github.io/chinese-international-student-career-guide/` → `scripts/check_seo.py` → `scripts/check_pages_links.py`。生成结果由 Pages Actions 在运行环境中发布，并核对线上 SHA-256。
3. 对成品执行 `python3 scripts/check_seo.py` 和 `python3 scripts/check_pages_links.py`。后者模拟 `/chinese-international-student-career-guide/` 子路径，核对 HTML/CSS 本地资源、HTML 锚点和必须下载的文件；不访问互联网，不验证政策或外部来源。
4. 将本项目的源码、经 QA 的成品 PDF、模板、本发布文档与工作流提交。仓库中已有的 `dist/` 仅作快照；发布产物由 Actions 重新构建。不要把 `.git`、凭据、会话临时目录或个人申请资料作为网站成品发布。

必须存在且非空的下载文件：

- `dist/downloads/chinese-international-student-career-guide.pdf`
- `dist/templates/career-workbook.xlsx`
- `dist/downloads/editable-templates.zip`
- `dist/downloads/source-code.zip`

## GitHub 设置和推送

确认精确仓库 `AIPMAndy/chinese-international-student-career-guide` 已存在且属于 AIPMAndy；若尚未创建，在具备建仓操作的已授权会话中创建此独立公开仓库。新建接口缺失不应被描述为“用户未授权”。

在本仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。工作流在 `main` 的正文、数据、模板、网站样式/脚本、打包/构建/检查脚本、PDF 下载文件或 Pages 工作流更新后自动执行，也可手动运行；只允许本仓库的 `main` 发布。

工作流从源文件生成新的网站与两个 ZIP，在运行环境中校验 canonical、OG、JSON-LD、robots、sitemap、站内链接和必要文件；PDF 仍复用仓库中已交付的二进制文件，不在 Pages 作业重排 PDF。部署作业仅取得 `contents: read`、`pages: write`、`id-token: write`，使用 `github-pages` 环境。

## 完成标准

1. GitHub 返回的 `main` 提交 SHA 与本次发布提交一致；Actions 生成的 `dist/` 与历史提交快照可能不同，不能用旧快照 SHA 代替实际运行的校验结果。
2. 此提交的 Pages 工作流状态为成功，并取得部署实际返回的 `page_url`。
3. 实际网站首页、至少一个章节页、CSS/JS、PDF、XLSX 和 ZIP 下载返回 HTTP 200，且与当轮 Actions 生成物 SHA-256 相同；不能只根据预计 URL 或工作流存在断言上线。
4. 在手机宽度检查导航、正文、横向表格与下载入口。页内公众号、微信和官网使用已核实的公开品牌信息。

本地校验完成与线上发布是两个独立状态。没有上述远程证据时，发布状态保持“待推送 / 待部署 / 待线上验收”，如实列明当前阻碍。

## 官方依据

2026-11-13 核对：

- [配置 GitHub Pages 发布来源](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [使用 GitHub Pages 自定义工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)

## 2026-11-14 源码驱动 SEO 发布

- [提交 f629b32](https://github.com/AIPMAndy/chinese-international-student-career-guide/commit/f629b32eda80c73ab3e439ec8751afc67d6fbd26) 触发 [Actions #43519219464](https://github.com/AIPMAndy/chinese-international-student-career-guide/actions/runs/43519219464)：重建来源包和 50 个 HTML，SEO/GEO 元数据及站内链接校验无报错，Pages 部署成功。发布后首页、章节、CSS、JS、PDF、XLSX、两个 ZIP 共 8 个 URL 均实际返回 HTTP 200 且 SHA-256 与本次构建产物一致。
- 本轮线上 PDF SHA-256 是 `053a534012414f8a2efd95213ded1f785d7ef505f33595832bc5fac39778d478`（674,016 字节）。仓库既有的 81 页逐页视觉审阅、字体与注释验证记录绑定的是另一个 SHA-256（`f1f3a332d24505b198222a7186694e9aff633285d58557316e4cb6ce38f4201f`）。在重新对当前线上 PDF 进行逐页 QA 前，不能把旧审阅结论视为当前 PDF 的证明。
- 新服务入口指向 `https://metaver.vip/services`；页面底部保留个人官网、公司官网，首页继续提供微信 `AIPMAndy` 复制动作。独立手机和视觉复测仍待执行，不能因此标为全站 DONE。
