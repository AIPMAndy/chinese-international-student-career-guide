# 网站构建与检查

网站为多页静态 HTML，不依赖外部字体、脚本或在线数据库。正文存在于生成的 HTML 中，关闭 JavaScript 仍可阅读全部内容、打开章节与下载文件。JavaScript 仅用于菜单、地区筛选、复制微信号和打印。

## 构建

```bash
python3 scripts/build_site.py
```

可选参数：

```bash
python3 scripts/build_site.py --base-url https://YOUR-PUBLISHED-SITE
```

确认真实 GitHub 仓库发布后，增加 `--repo-url`，导航才显示开源仓库链接。不要预填未创建地址。

内容来源：

- `content/core/*.md`：通用实操。
- `content/regions/*.md`：地区正文。
- `data/coverage-*.json`：地区核验深度与缺口。
- `data/sources-*.json`：来源登记。
- `templates/`：可编辑模板与文字材料。
- `downloads/`：PDF、模板包及源文件包。

构建自动发现新文件。输出在 `dist/`。下载入口只在对应文件存在时启用，缺失文件显示制作状态。

## 静态验证

```bash
python3 website/check_links.py
```

检查全部 HTML 的本地文件链接、片段锚点、重复元素ID及唯一主标题，结果写入 `website/static-validation.json`。这个检查不把外部链接存在当作政策核验。

## 浏览器验证

安装并配置 Playwright 与 Chromium 的环境可运行：

```bash
python3 -m http.server 8124 --directory dist
node website/validate_site.mjs . http://127.0.0.1:8124 /tmp/career-site-review
```

Chromium 默认路径 `/usr/bin/chromium`，可通过环境变量 `CHROMIUM_PATH` 指定。脚本以 390×844 视口逐页检查横向溢出、标题、HTTP响应、地区筛选、移动菜单与工作簿下载，同时生成桌面与手机截图。

制作环境中，Playwright 包可调用，但系统 Chromium 因 `socket() failed: Operation not permitted` 未能启动；原生 Chrome 的 DevTools 也被组织策略禁用。没有绕过这些限制。

因此改用同一浏览器、同源页面内的 390 / 375 CSS px 视口实测响应式布局。实际操作验证了移动导航、地区组合筛选、正文表格局部横向滚动和工作簿下载；首页及下载页没有整页横向溢出。桌面滚动条占用宽度后，实际文档宽分别为 375 / 360 px，均等于文档 `scrollWidth`。

记录见 `website/mobile-validation.json`，截图见 `website/review/mobile-390-375.jpg`。此项是窄视口实际渲染验证，不冒充真实 iOS / Android 设备或移动 Safari 测试。临时视口检查页已删除。PDF 和 ZIP 完成后的下载、部署后的实际访问仍由最终发布验证记录覆盖。

## 维护原则

先更新 Markdown 与来源登记，再重新生成网站和 PDF。每条政策同时保留适用地区、条件与核验日期。不要只改 HTML 而留下内容源与 PDF 不一致。
