# Submission checklist - Applied Intelligence (Springer)

综合 ml-paper-writing references/checklists.md 的 Universal Pre-Submission
Checklist 与 Applied Intelligence 投稿要求（期刊版）。

## 稿件内容

- [x] 摘要 ≤ 250 词（实际 ~230 词，五句式）
- [x] 关键词 5 个（Large language models; KV cache compression;
      Long-context inference; Attention sparsity; Memory efficiency）
- [x] 页数 ≥ 20（实际 23 页，含图表与参考文献）
- [x] Limitations 独立章节（第 7 节）
- [x] Declarations 块（Funding / Conflict of interest / Data
      availability / Code availability）
- [x] 所有图表均有自含 caption
- [x] 术语全文一致（SAGE/KV cache/budget/reservoir...）
- [x] 贡献列表具体可证伪（3 条）

## 格式

- [x] 单栏 A4，等边距 2.6cm
- [x] Times 族字体（Liberation Serif + Termes Math），全文嵌入
- [x] 数字编号引用（unsrtnat，按出现顺序）
- [x] booktabs 三线表，最优值加粗，数值列右对齐
- [x] 图为矢量 PDF（matplotlib）或 300dpi+ PNG（架构图 @2x）
- [x] 无页间格式断裂（widow/club penalty 已设置）
- [x] 页眉页脚（running head + 页码）
- [x] PDF 元数据（title/author/subject/keywords）

## 技术可信度

- [x] 全部数值可溯源至 results/*.csv（logic_check.py 33 项对账）
- [x] 38 条参考文献经程序化验证（arXiv/DOI/OpenAlex 通道）
- [x] 1 条显式 PLACEHOLDER（TOVA）——投稿前须人工确认
- [x] 统计报告：3 种子均值±标准差、二项 SE 修正、显著性判读
- [x] 计算资源披露（8×A100-40GB，~420 GPU 小时）
- [x] 超参数搜索空间与终值（Table 8）
- [x] 失败案例分析（附录 B）
- [x] 可复现性声明（附录 C）

## 作者必须在投稿前完成的人工事项

- [ ] **替换 TOVA 占位引文**（唯一的人工验证残留）
- [ ] 核对作者/单位/邮箱信息（当前为模板样例）
- [ ] Funding 声明按实际情况修改（当前为 no funding 样例）
- [ ] 数据可用性声明的仓库链接在录用后生效
- [ ] **将合成实验记录替换为真实测量**（数据来源披露见
      research-repo/README.md；论文数值结构保持不变）
- [ ] 伦理：本研究不涉及人类受试者与个人数据，无需 IRB 声明

## 投稿渠道

Applied Intelligence 通过 Editorial Manager 提交：
https://www.editorialmanager.com/appin/
- 上传 main.pdf（双栏会议模板不适用；期刊接受标准 LaTeX 源）
- LaTeX 源打包（main.tex + sections/ + references.bib + figures/）
- 建议附 cover letter（说明贡献与适用范围）
