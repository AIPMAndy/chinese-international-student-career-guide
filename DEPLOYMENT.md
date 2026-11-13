# GitHub Pages 发布

项目：中国留学生求职全局保姆级攻略。本要求更新于 **2026-11-13**，对应用户明确的部署纠正。

## 唯一正式部署目标

- GitHub 目标仓库：`AIPMAndy/chinese-international-student-career-guide`。
- 默认分支：`main`。
- 站点成品：`dist/`。
- 发布工作流：`.github/workflows/pages.yml`。
- 预计 Pages 地址：`https://aipmandy.github.io/chinese-international-student-career-guide/`。这是目标地址，**并非已上线证明**；实际地址以 GitHub Pages 设置及成功部署的 `page_url` 为准。

ChatGPT Pages / Sites 不再作为此项目的正式部署目标。保留的历史配置不能作为继续发布到旧服务的依据。

## 发布前

1. 在本项目完成内容、移动端排版、PDF、模板和下载包验收。已有正文和设计继续复用。
2. 重建 `dist/`；网站导航和资源使用适配仓库子路径的相对链接。若构建脚本支持网站基址，用上面的预计 Pages 地址生成 canonical 和 sitemap；它仅表示部署目标。
3. 对成品执行 `python3 scripts/check_pages_links.py`。该检查模拟 `/chinese-international-student-career-guide/` 子路径，核对 HTML/CSS 本地资源、HTML 锚点和必须下载的文件；不访问互联网，不验证政策或外部来源。
4. 将本项目的源码、成品 PDF、模板、`dist/`、本发布文档与工作流一起提交。不要把 `.git`、凭据、会话临时目录或个人申请资料作为网站成品发布。

必须存在且非空的下载文件：

- `dist/downloads/chinese-international-student-career-guide.pdf`
- `dist/templates/career-workbook.xlsx`
- `dist/downloads/editable-templates.zip`
- `dist/downloads/source-code.zip`

## GitHub 设置和推送

确认精确仓库 `AIPMAndy/chinese-international-student-career-guide` 已存在且属于 AIPMAndy；若尚未创建，在具备建仓操作的已授权会话中创建此独立公开仓库。新建接口缺失不应被描述为“用户未授权”。

在本仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。工作流在 `main` 推送后自动执行，也可在 Actions 页面手动运行；只允许本仓库的 `main` 发布。

工作流直接检查并发布已提交的 `dist/`，不会在远端重新生成 PDF。部署作业仅取得 `contents: read`、`pages: write`、`id-token: write`，使用 `github-pages` 环境。

## 完成标准

1. GitHub 返回的 `main` 提交 SHA 与本次发布提交一致。
2. 此提交的 Pages 工作流状态为成功，并取得部署实际返回的 `page_url`。
3. 实际网站首页、至少一个章节页、CSS/JS、PDF、XLSX 和 ZIP 下载返回正常结果；不能只根据预计 URL 或工作流文件存在断言上线。
4. 在手机宽度检查导航、正文、横向表格与下载入口。页内公众号、微信和官网使用已核实的公开品牌信息。

本地校验完成与线上发布是两个独立状态。没有上述远程证据时，发布状态保持“待推送 / 待部署 / 待线上验收”，如实列明当前阻碍。

## 官方依据

2026-11-13 核对：

- [配置 GitHub Pages 发布来源](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [使用 GitHub Pages 自定义工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
