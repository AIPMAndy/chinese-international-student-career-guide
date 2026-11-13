# 2026-11-14 · 已发布 PDF 当前二进制复核记录

## 绑定文件与证据

- 正式站点：[GitHub Pages](https://aipmandy.github.io/chinese-international-student-career-guide/)
- 已部署 PDF：[在线完整读本](https://aipmandy.github.io/chinese-international-student-career-guide/downloads/chinese-international-student-career-guide.pdf)
- 当前已发布文件 SHA-256：`053a534012414f8a2efd95213ded1f785d7ef505f33595832bc5fac39778d478`；文件长度 674,016 字节
- [当前版本 PDF CI #43519672476](https://github.com/AIPMAndy/chinese-international-student-career-guide/actions/runs/43519672476) 成功；[下载 81 页渲染与机器报告](https://github.com/AIPMAndy/chinese-international-student-career-guide/actions/runs/43519672476/artifacts/14082377823)
- [实际 Pages 部署 #43519219464](https://github.com/AIPMAndy/chinese-international-student-career-guide/actions/runs/43519219464)：线上 PDF HTTP 200、SHA-256 与当次 Actions 构建产物一致。

## 本轮实际复核

1. 从本次 PDF CI 下载原始归档，核对归档中 PDF SHA-256 与实际 Pages 检测结果完全相同。
2. 对归档内 41 组双页图进行总览审阅，覆盖第 1–81 页；另放大检查第 1–2 页封面与目录、第 39–40 页地区页、第 63–64 页中英文简历模板及第 81 页最后服务入口页。总览未发现明显的空白丢失页、整页溢出、字体方框、章节错序或异常版式断裂；放大样本中标题、表格、正文边距与页码可辨。
3. 当前 SHA 的自动化结构核对结果：**81 页、50 书签、122 内部链接、191 外部链接**；文字均可提取，页面边界、目录目标、字体嵌入、官方双官网超链接以及微信 `AIPMAndy` 均通过，未报告错误。详见本次 CI 产物中的 `docs/pdf-validation.json`。
4. 现有 Markdown 仍是 PDF 内容权威源，生成器为 `scripts/build_pdf.py`，校验器为 `scripts/validate_pdf.py`。本轮未修改 PDF 正文，不需要虚构一个新 PDF 内容版本。

## 待补充 / 验收边界

- 上述 41 组缩略图覆盖全部页面，但不等同于把 81 页逐页放大检查细微断字、标点或低对比度；需要对当前 SHA 全页高倍率终审后才能标记“PDF 视觉 DONE”。
- 仓库先前 1–81 页的逐页审阅记录绑定的是旧 SHA `f1f3a332d24505b198222a7186694e9aff633285d58557316e4cb6ce38f4201f`，**不可冒充当前 SHA 的完整人工视觉证明**。
- iOS Safari / 安卓原生 PDF 阅读器、纸质打印和双官网外部目标持续可访问性没有在本轮建立实测证据。

当前 PDF 状态：**已发布、机器校验与全页总览通过；高倍率全页视觉和实机阅读待完成**。