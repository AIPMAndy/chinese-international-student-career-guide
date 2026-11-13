# v1.0.0 验证记录与真实边界

日期：2026-11-13。项目：中国留学生求职全局保姆级攻略。作者：AI 酋长 Andy。

## 内容与来源

已完成16个通用章、20个境外地区正文及回国路线，共21条已有路线；另列20个待补充地区导航。16条路线标为“已核验基础路径”，5条已有正文路线仍标为“待补充”。没有声称所有国家或所有身份分支均已覆盖。

官方来源90条：75条已核验其登记支持范围，15条保留部分读取、动态页面或规则冲突限制。来源URL、适用范围、核验日期、支持结论与已知限制保存在 `data/sources-*.json`。全部正文引用编号与登记网址的结构核对结果见 [content-validation.json](content-validation.json)。原文读取记录及限制见 [西部地区研究](research-west.md) 与 [亚洲及大洋洲研究](research-east.md)。

资料限制没有被改写成“全部链接通过”。芬兰申请期限说明、新西兰未来生效日期、韩国新旧页面等冲突保留在正文；动态招聘页只支持实际取得的范围。

## PDF

最终81页，50个书签，122处内部跳转，191处外部链接注释。正文所用中文字体已嵌入；当前字符覆盖缺字为0；自动提取检查无页外文本、替代字符或空页。完整结果及SHA256见 [pdf-validation.json](pdf-validation.json)。

全部81页实际渲染并逐页查看，分工记录为 [1–28页](pdf-review-west.md)、[29–49页](pdf-review-root.md)、[50–81页](pdf-review-east.md)。已修复简历代码块换行与极稀疏章末页。保留一项不阻断使用的细节：第9页个别问号独占换行。

## 可编辑模板

工作簿9张表，含8类工具和使用说明；另有8份CSV、双语邮件、材料骨架、AI提示词与路线填写单。12项输入与公式边界检查通过；最终公式错误为0；全部输入留空，测试数据已清理。检查范围见 [template-validation.md](template-validation.md)。

未在桌面Excel、WPS和Google Sheets中逐一完成原生交互兼容性实测。CSV不含公式、下拉和格式。现有XLSX和文本文件均可直接编辑；原始工作簿生成脚本依赖制作环境的artifact-tool，未承诺普通npm环境可重建。

## 网站与下载

50个静态HTML页面，正文直接写在HTML中。全部本地链接和锚点检查见 [static-validation.json](../website/static-validation.json)；地区导航计数见 [coverage-validation.json](../website/coverage-validation.json)。下载包的CRC及SHA256见 [release-manifest.json](../downloads/release-manifest.json)。

已在实际浏览器内使用390/375 CSS px同源窄视口，操作导航、地区筛选、搜索、正文表格横滚和工作簿下载；首页与下载页没有整页横向溢出。方法、截图与限制见 [mobile-validation.json](../website/mobile-validation.json)。这不是物理手机、iOS Safari或触摸实机测试。

公开网站已上线并实际访问：[在线攻略](https://aipmandy.github.io/chinese-international-student-career-guide/)，[免费资源与下载](https://aipmandy.github.io/chinese-international-student-career-guide/downloads)。

首次公开部署后，对全部73个静态文件进行无登录、无Cookie的HTTP GET：全部200，响应文件SHA256全部与当次发布的本地文件一致，详见 [live-http-validation.json](live-http-validation.json)。随后增加的验收文档与截图会进入源码包，源码包当前哈希以 `downloads/release-manifest.json` 为准；首次部署记录保留其原始版本与哈希，不回填为后续版本。

实际浏览器操作确认：首页与下载页可访问；PDF、XLSX、模板ZIP、源码ZIP四个按钮均完成下载事件；全部地区41、亚洲15、亚洲待补充12的筛选结果正确。截图见 [live-homepage.jpg](../website/review/live-homepage.jpg)，部署与UI记录见 [publication-verification.json](publication-verification.json)。

另将源码ZIP解压到新临时目录，使用所附字体与XLSX，成功重建81页PDF、两个ZIP和50个静态HTML；无需私有工作簿生成运行时即可复现已交付网站与读本。结果见 [source-rebuild-validation.json](source-rebuild-validation.json)。

## GitHub 与修改范围

只读检查AIPMAndy现有仓库，重点读取两个指定项目的目录和相关正文，见 [repository-audit.md](repository-audit.md)。候选名称在本次可见范围未发现冲突。全部写入位于本任务新项目；未修改个人主页、总导航、个人网站或其他已有仓库。

GitHub 公开仓库 [AIPMAndy/chinese-international-student-career-guide](https://github.com/AIPMAndy/chinese-international-student-career-guide) 已创建，源码、PDF、模板与网站已推送。正式网站采用 [GitHub Pages](https://aipmandy.github.io/chinese-international-student-career-guide/)。

[Pages 成功运行](https://github.com/AIPMAndy/chinese-international-student-career-guide/actions/runs/43487144595) 对应提交 `0d22d503acc99760e3950172946dab471c0521ba`。本次发布先检查 50 个 HTML 页面、2,032 个引用及必需下载，再对首页、正文、CSS、JS、PDF、XLSX、模板 ZIP 与源码 ZIP 共 8 个实际 URL 发起 HTTP GET；均返回 200，且 SHA-256 与此提交的 `dist/` 一致。

此前未建仓、未登录以及早期预览的记录属于历史阶段，不再代表当前发布状态。上述新工作流日志是本次 GitHub Pages 访问与下载验证依据；此前 `live-http-validation.json` 保留为历史记录，不作为本次提交的重新验收。实体手机、Excel/WPS 原生兼容性边界保持不变。

## 地区缺口

已有正文但仍待补充：澳门、台湾、韩国、马来西亚、阿联酋。仅列导航且尚未核验：墨西哥、哥斯达黎加、丹麦、挪威、意大利、西班牙、葡萄牙、比利时、奥地利、波兰、捷克、泰国、越南、印度尼西亚、菲律宾、印度、沙特阿拉伯、卡塔尔、斐济、巴布亚新几内亚。

各地仍有职业准入、家属、历史身份、雇主批次和地方规则等未展开事项。完整清单与补充方法见 [地区覆盖缺口](../content/core/15-coverage-gaps.md)。非洲与南美洲不在本版范围。
