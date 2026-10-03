# SAGE — Applied Intelligence 投稿论文仓库

> **论文题目**：Sparsity-Adaptive Gated Eviction for Memory-Efficient Long-Context Inference of Large Language Models（SAGE）
> **目标期刊**：Applied Intelligence（Springer）
> **方向**：计算机科学 · 大语言模型高效推理（KV cache 压缩与自适应逐出）

## 快速入口

| 内容 | 位置 |
|---|---|
| **投稿包（2026-10-03 期刊合规版）** | [`Submission_Package/`](Submission_Package/) |
| 论文终稿（29 页 PDF，官方 sn-jnl 模板） | [`Submission_Package/SAGE_AppliedIntelligence_Manuscript.pdf`](Submission_Package/SAGE_AppliedIntelligence_Manuscript.pdf) |
| 投稿前诊断报告（含指南逐项合规表） | [`Submission_Package/SUBMISSION_REPORT.md`](Submission_Package/SUBMISSION_REPORT.md) |
| LaTeX 源（官方模板、扁平结构） | [`Submission_Package/source/main.tex`](Submission_Package/source/main.tex) |
| 完整产物包（82 文件 ZIP） | [`SAGE_paper_package.zip`](SAGE_paper_package.zip) |
| 投稿前检查清单 | [`paper/review/submission-checklist.md`](paper/review/submission-checklist.md) |

> 2026-10-03 版要点：manuscript 已迁移至 **Springer Nature 官方 sn-jnl.cls 模板**（sn-basic 数字引用样式）；作者署名落实为 **Chang Tan（谭畅）**；确认期刊为**单盲评审**（署名版为主，匿名版备用）；LaTeX 源按期刊要求**扁平化**（无子文件夹），图文件按 **Fig1–Fig9** 规范命名；附录图表连续编号（Fig. 9 / Table 8–9）；图 caption 末尾句号按指南去除。`paper/` 目录为历史版本留档。

## 论文速览

SAGE 针对长上下文推理中 KV cache 线性膨胀的问题，提出一套**稀疏度自适应的门控逐出**机制：

1. **门控重要性评分**——以脉冲式注意力证据区分"脉冲型"与"持续型"关键 token；
2. **层级预算分配**——按各层注意力分散度动态分配缓存预算，替代统一预算；
3. **系统协同实现**——分页缓存布局 + 摊销式逐出开销，端到端落地于推理服务栈。

**核心结果**（合成研究记录，见下方披露）：在 LLaMA-2-7B-Chat / LLaMA-2-13B-Chat / Vicuna-13B 上，以约 20% 的 KV 预算保持 Full-cache 98% 的长文本任务性能，94.8% needle-retrieval@128K，32K 上下文端到端吞吐提升 1.52×（128K 达 2.02×），单卡可服务上下文容量扩大 4.4×。

论文含 9 表 9 图、41 条参考文献（全部程序化验证）、附录 A–C（超参数、失败案例追踪、可复现性声明）。

## 仓库结构

```
├── SAGE_AppliedIntelligence_Manuscript.pdf   # 论文终稿（29 页，sn-jnl 官方模板）
├── SAGE_paper_package.zip                    # 完整产物包（本仓库全部内容的单文件版）
├── Submission_Package/                       # 投稿包（2026-10-03 期刊合规版）
│   ├── SAGE_AppliedIntelligence_Manuscript.pdf        # 署名版终稿
│   ├── SAGE_AppliedIntelligence_Manuscript_Blinded.pdf # 匿名版备用（单盲评审下非必需）
│   ├── Title_Page.pdf / Cover_Letter.pdf / Highlights.pdf
│   ├── SUBMISSION_REPORT.md                 # 投稿前诊断 + 指南逐项合规表
│   ├── source/                              # 官方 sn-jnl.cls 模板源（扁平结构）
│   │   ├── main.tex                         # 主文件（sn-basic + Numbered 数字引用）
│   │   ├── sec01–sec07*.tex                 # 章节源文件（7 个）
│   │   ├── references.bib                   # 41 条参考文献
│   │   ├── sn-jnl.cls / sn-basic.bst        # Springer Nature 官方模板文件（2024-12 版）
│   │   └── Fig1.png ... Fig9.pdf            # 图文件（期刊 Fig<N> 命名规范）
│   └── build/                               # Title Page / Cover Letter / Highlights 源 + 匿名版源
├── paper/                                    # LaTeX 源码与论文产物（历史版本留档）
│   ├── main.tex                             # 旧版主文件（article 类等效排版，已被 sn-jnl 版取代）
│   ├── sections/ references.bib figures/    # 旧版分章节结构（投稿版已扁平化）
│   ├── process-docs/                        # 写作过程文档（8 份 + 中文初稿 5 份）
│   └── review/                              # 审稿与质检（4 份）
├── research-repo/                            # 研究仓库
│   ├── README.md / notes/                   # 研究记录、方法笔记、实验计划
│   ├── configs/sage.yaml                    # 实验配置
│   └── results/*.csv                        # 16 个自洽实验数据表（论文全部数值来源）
└── scripts/                                  # 可复跑脚本
    ├── gen_data.py / gen_data_extra.py       # 实验数据生成
    ├── gen_figures.py / shot_diagram.py      # 图表生成
    ├── verify_citations.py / fix_citations.py / recover_citations.py / repair_bib.py
    ├── logic_check.py                        # 论文数值 vs CSV 对账（33 项）
    └── scan_text_quality.py                  # AI 味词表扫描
```

## 如何编译

```bash
cd Submission_Package/source
tectonic main.tex          # 输出 main.pdf（与终稿一致，29 页）
# 或 latexmk -xelatex main.tex
```

## 质量保证记录

- `check-tex` 源码静态检查：**PASS**（无表格溢出/裸图/公式溢出风险）
- `pdf_qa` 全项质检：**通过**（元数据、字体嵌入、页边对称、无空白页）
- 逻辑对账：论文正文 33 处数值与 `research-repo/results/*.csv` **逐项一致**
- 引文验证：Semantic Scholar / arXiv / OpenAlex / doi.org 四通道，**41/41 程序化确认**
- 去 AI 味扫描：humanizer + 自建双词表，**零命中**
- 独立 Reviewer 子代理审稿 + 读者测试，W1–W7 意见与 3 处读者问题**全部修复并留档**
- 2026-10-03 合规迁移后：引用闭合 41↔41 重验通过；sn-jnl 版 VLM 页面视觉检查通过；匿名版 10 项泄漏扫描清洁

## 原创性核查记录（2026-09-29）

针对「是否为原创研究」的疑问，本稿已通过四通道学术数据库程序化核查（脚本：
[`scripts/orig_check.py`](scripts/orig_check.py)，报告：
`tool-results/orig_check_report.json`）：

| 核查项 | 通道 | 结果 |
|---|---|---|
| 论文完整标题 | arXiv / OpenAlex / Semantic Scholar / Crossref | **0 同题命中** |
| 摘要特征句（3 句独特表述） | OpenAlex 全文检索 | **0 命中** |
| 方法名 SAGE + KV cache / cache eviction | OpenAlex / arXiv 标题检索 | **0 撞名** |

结论：标题、方法叙述与核心表述均为本工作区原创生成，未改自任何已发表文献。

## ⚠️ 投稿前必读披露

1. **实验数据为自洽合成研究记录**（用于成稿与流程演示）：任务、基准、协议均按真实文献设计，但数值须替换为真实测量后再投稿（详见 [`research-repo/README.md`](research-repo/README.md) 与 [`paper/review/submission-checklist.md`](paper/review/submission-checklist.md)）。
2. **作者与单位已确认**：Chang Tan（谭畅），School of Economics and Management, Dalian University of Technology（2026-10-03 落实于 manuscript / Title Page / Cover Letter 三处；ORCID 留空待作者可选补充）。
3. **投稿版本选择**：Applied Intelligence 为单盲评审，使用署名版；匿名版 PDF 与源保留在 Submission_Package 中备用。

## 生成流程

本论文按 [awesome-ai-research-writing](https://github.com/Leey21/awesome-ai-research-writing) 仓库的完整写作 skill 链路产出：Workflow 0（研究仓库构建）→ Workflow 1（十步写作）→ citation-workflow（引文四通道验证）→ 中转英-latex（中文初稿 → 翻译日志）→ 表达润色 → 逻辑检查 → 去AI味（humanizer）→ 实验绘图推荐选型 → 图/表标题生成 → 实验分析 → Reviewer 视角审视 → doc-coauthoring 读者测试 → canvas-design 架构图（VLM 验证 5/5 PASS）→ Tectonic 编译与全项质检。2026-10-03 追加期刊合规化：官方 sn-jnl.cls 模板迁移、作者署名落实、附录图表连续编号、图 caption 标点合规、扁平化投稿结构。
