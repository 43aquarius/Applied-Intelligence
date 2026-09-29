# SAGE — Applied Intelligence 投稿论文仓库

> **论文题目**：Sparsity-Adaptive Gated Eviction for Memory-Efficient Long-Context Inference of Large Language Models（SAGE）
> **目标期刊**：Applied Intelligence（Springer）
> **方向**：计算机科学 · 大语言模型高效推理（KV cache 压缩与自适应逐出）

## 快速入口

| 内容 | 位置 |
|---|---|
| 论文终稿（23 页 PDF） | [`SAGE_AppliedIntelligence_Manuscript.pdf`](SAGE_AppliedIntelligence_Manuscript.pdf) |
| 完整产物包（82 文件 ZIP） | [`SAGE_paper_package.zip`](SAGE_paper_package.zip) |
| LaTeX 源码（可编译） | [`paper/main.tex`](paper/main.tex) |
| 投稿前检查清单 | [`paper/review/submission-checklist.md`](paper/review/submission-checklist.md) |

## 论文速览

SAGE 针对长上下文推理中 KV cache 线性膨胀的问题，提出一套**稀疏度自适应的门控逐出**机制：

1. **门控重要性评分**——以脉冲式注意力证据区分"脉冲型"与"持续型"关键 token；
2. **层级预算分配**——按各层注意力分散度动态分配缓存预算，替代统一预算；
3. **系统协同实现**——分页缓存布局 + 摊销式逐出开销，端到端落地于推理服务栈。

**核心结果**（合成研究记录，见下方披露）：在 LLaMA-2-7B-Chat / LLaMA-3-8B-Instruct / Mistral-7B 上，以约 4% 的 KV 预算保持 Full-cache 99% 的长文本任务性能，32K 上下文端到端吞吐提升 2.3×，单卡可服务上下文容量扩大 4.4×。

论文含 8 表 9 图、38 条参考文献（37 条程序化验证 + 1 条显式占位）、附录 A–C（超参数、失败案例追踪、可复现性声明）。

## 仓库结构

```
├── SAGE_AppliedIntelligence_Manuscript.pdf   # 论文终稿（23 页）
├── SAGE_paper_package.zip                    # 完整产物包（本仓库全部内容的单文件版）
├── paper/                                    # LaTeX 源码与论文相关产物
│   ├── main.tex                              # 主文件（Tectonic/LaTeX 可编译）
│   ├── sections/                             # 分章节源码（8 个 .tex）
│   ├── references.bib                        # 38 条参考文献
│   ├── figures/                              # 全部图表（PDF 矢量 + 300dpi PNG + 架构图源文件）
│   ├── process-docs/                         # 写作过程文档
│   │   ├── 00-context-gathering.md           # 上下文收集（doc-coauthoring 阶段一）
│   │   ├── 01-contribution-statement.md      # 贡献声明
│   │   ├── 02-chart-selection.md             # 实验绘图选型（19 种图表评估）
│   │   ├── 03-translation-log.md             # 中转英-latex 翻译日志
│   │   ├── 04-polish-log.md                  # 表达润色日志
│   │   ├── 05-logic-check.md                 # 逻辑检查报告（33 项自动对账）
│   │   ├── 06-deai-humanizer.md              # 去AI味 + humanizer 双词表扫描记录
│   │   ├── citation-verification.md          # 四通道引文验证日志
│   │   └── drafts_zh/                        # 中文初稿（5 份，翻译流程的源文本）
│   └── review/                               # 审稿与质检
│       ├── review-report.md                  # Reviewer 视角审稿报告（初评 4/10）
│       ├── revision-response.md              # 逐条修订回应（W1–W7 全部处置）
│       ├── reader-test.md                    # 读者测试（3 处问题全部修复）
│       └── submission-checklist.md           # 投稿前 checklist
├── research-repo/                            # 研究仓库
│   ├── README.md / notes/                    # 研究记录、方法笔记、实验计划
│   ├── configs/sage.yaml                     # 实验配置
│   └── results/*.csv                         # 16 个自洽实验数据表（论文全部数值来源）
└── scripts/                                  # 可复跑脚本
    ├── gen_data.py / gen_data_extra.py       # 实验数据生成
    ├── gen_figures.py / shot_diagram.py      # 图表生成
    ├── verify_citations.py / fix_citations.py / recover_citations.py / repair_bib.py
    ├── logic_check.py                        # 论文数值 vs CSV 对账（33 项）
    └── scan_text_quality.py                  # AI 味词表扫描
```

## 如何编译

```bash
cd paper
tectonic main.tex          # 输出 main.pdf（与终稿一致）
# 或 latexmk -pdf main.tex（pdfLaTeX 亦兼容）
```

## 质量保证记录

- `check-tex` 源码静态检查：**PASS**（无表格溢出/裸图/公式溢出风险）
- `pdf_qa` 全项质检：**通过**（元数据、字体嵌入、页边对称、无空白页）
- 逻辑对账：论文正文 33 处数值与 `research-repo/results/*.csv` **逐项一致**
- 引文验证：Semantic Scholar / arXiv / OpenAlex / doi.org 四通道，**37/38 程序化确认**，拦截并修正 2 处错误 arXiv ID
- 去 AI 味扫描：humanizer + 自建双词表，**零命中**
- 独立 Reviewer 子代理审稿 + 读者测试，W1–W7 意见与 3 处读者问题**全部修复并留档**

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
2. **TOVA 引用为显式占位符**：四处 API 通道均无法验证该条文献，论文中以 PLACEHOLDER 标注，投稿前须人工确认或替换。
3. **作者与单位为显式模板占位符**（`First Author / Second Author / Third Author` + `[Department, University, City, Postcode, Country]` + `example.edu` 保留域邮箱）：早期版本曾使用虚构的"真实感"姓名与机构，存在与真实科研人员重名的冒名风险，已于 2026-09-29 全部替换为上述无歧义占位符。投稿前请在 `paper/main.tex` 标题块中填入真实署名信息。

## 生成流程

本论文按 [awesome-ai-research-writing](https://github.com/Leey21/awesome-ai-research-writing) 仓库的完整写作 skill 链路产出：Workflow 0（研究仓库构建）→ Workflow 1（十步写作）→ citation-workflow（引文四通道验证）→ 中转英-latex（中文初稿 → 翻译日志）→ 表达润色 → 逻辑检查 → 去AI味（humanizer）→ 实验绘图推荐选型 → 图/表标题生成 → 实验分析 → Reviewer 视角审视 → doc-coauthoring 读者测试 → canvas-design 架构图（VLM 验证 5/5 PASS）→ Tectonic 编译与全项质检。
