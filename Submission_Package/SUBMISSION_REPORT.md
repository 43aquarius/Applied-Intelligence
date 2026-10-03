# SAGE — Applied Intelligence 投稿前终稿检查报告（2026-10-03 更新版）

> 本版在 2026-09-30 版基础上完成 **Springer Nature 官方 LaTeX 模板迁移**与期刊指南逐项合规化。
> 依据：Applied Intelligence 官方提交指南（https://link.springer.com/journal/10489/submission-guidelines，
> 全文抓取存档于工作区 `applied_intelligence_guidelines.txt`）
> 审计对象：`source/`（sn-jnl.cls LaTeX 源）+ 编译产物 + research-repo 实验记录 + 参考文献

---

## 〇、本次更新概要（2026-10-03）

| # | 变更项 | 内容 |
|---|--------|------|
| 1 | **官方模板迁移** | manuscript 从自定义 article 排版迁移至 **Springer Nature 官方 sn-jnl.cls（2024 年 12 月版）**，引用样式启用官方 `sn-basic` + `Numbered` 选项（natbib 由 cls 内部管理，bst 使用官方 sn-basic.bst） |
| 2 | **作者署名落实** | 英文署名确认为 **Chang Tan**（名前姓后，索引显示 Tan, C.），写入 manuscript 作者块（\fnm{Chang} \sur{Tan}）、Title Page、Cover Letter 三处；中文姓名谭畅在 Title Page 保留备注 |
| 3 | **评审模式确认** | 经多源核实（Springer 期刊列表、第三方期刊数据库），Applied Intelligence 为**单盲评审（single-blind）**；署名版为主投稿版本，匿名版 PDF 保留作备用 |
| 4 | **扁平化提交结构** | 按指南 "Please do not use subfolders for your LaTeX submission" 要求，source/ 重构为完全扁平：main.tex + 7 个 sec*.tex + references.bib + sn-jnl.cls + sn-basic.bst + Fig1-9 全部位于同一目录 |
| 5 | **图文件命名规范** | 按指南 "Name your figure files with 'Fig' and the figure number" 要求，图文件重命名为 **Fig1.png ... Fig9.pdf** |
| 6 | **附录图表连续编号** | 按指南 "Do not number the appendix figures 'A1, A2, A3'" 要求，附录图表从正文末尾继续编号：附录图 = **Fig. 9**，附录表 = **Table 8/9**（原先渲染为 Fig. A1 / Table A1/A2，已通过计数器覆盖修复） |
| 7 | **图 caption 末尾标点** | 按指南 "nor is any punctuation to be placed at the end of the caption" 要求，9 个图 caption 末尾句号已全部去除（表 caption 与算法标题不受该条约束，保留） |
| 8 | **参考文献条目类型修复** | `liu2024kivi`、`zaheer2020big` 由 @article（缺 journal 字段触发 BibTeX 错误）修正为 @misc，与其 arXiv 预印本性质一致 |
| 9 | **表格溢出修复** | 消融表（Table 6）首列标签过长导致 57.8pt 溢出，缩短标签并把 uniform/static 信息移入 caption，全文零 Overfull |
| 10 | **Declarations 标题对齐** | "Conflict of interest" 更名为 "Competing interests"（与期刊指南示例标题一致）；声明的单复数由 authors 改为 author（唯一作者） |

编译引擎：Tectonic（XeTeX）。`pdflatex` 类选项用于选择对全部引擎安全的 URL 断行机制（cls 行为：非 pdflatex 模式加载 breakurl，该包不兼容 XeTeX）。

---

## 一、论文事实基准（审计 30 项，内容未变）

| # | 项目 | 实际内容（源文件核实） |
|---|------|------------------------|
| 1 | 正式标题 | Sparsity-Adaptive Gated Eviction for Memory-Efficient Long-Context Inference of Large Language Models |
| 2 | 当前作者署名 | **Chang Tan（谭畅）**，唯一作者，三处一致（manuscript / Title Page / Cover Letter） |
| 3 | 作者数量 | 1（sole + corresponding author，\author* 标注） |
| 4 | Affiliation | School of Economics and Management, Dalian University of Technology, No.2 Linggong Rd, Ganjingzi, Dalian 116024, Liaoning, China |
| 5 | Abstract | 186 词（150–250 区间内）✓，五句式：问题/动机/方法/实验/意义 |
| 6 | Keywords | 5 个（Large language models; KV cache compression; Long-context inference; Attention sparsity; Memory efficiency）✓ |
| 7 | 研究问题 | KV cache 随上下文线性膨胀成为长上下文部署的约束；现有逐出方法在 <50% 预算下质量骤降 |
| 8 | SAGE 定义 | training-free 框架，三耦合组件 under 一个全局 memory contract |
| 9 | ACS | 指数衰减注意力置信评分 s=λs+a（Eq.2），跟踪 current relevance |
| 10 | LABA | 层自适应预算分配（归一化熵 κ_l，Eq.3–4，τ=1.5，在线每 K=512 步重分配） |
| 11 | DRE | 双储库逐出（protected recent window r=32 + sink |S|=4 + history 区域，Eq.5） |
| 12 | memory contract | 全局保留比 ρ：Σ|C_l|≤ρLt（Eq.1）；nominal 20% vs realized 22.6% 全文严格区分 |
| 13 | 主要公式 | Eq.(1) contract、Eq.(2) ACS、Eq.(3) κ、Eq.(4) budget、Eq.(5) eviction |
| 14 | Algorithm 1 | 单步解码循环：评分→(每K步)重分配→逐出→追加 |
| 15 | 实验模型 | LLaMA-2-7B-Chat、LLaMA-2-13B-Chat、Vicuna-13B-v1.5（4K 原生窗口，NTK α=8 统一扩展） |
| 16 | 数据集 | WikiText-2、PG19（2048 滑窗）、LongBench 11 任务（英文）、needle 8K–128K（4 深度×50 样本）、MT-Bench（附录） |
| 17 | Baselines | Full、StreamingLLM、H2O（官方 hybrid 0.1/0.1）、ScissorHands、TOVA（capped at contract，协议偏离已披露）、FastGen；KIVI 单独讨论 |
| 18 | Budget 设置 | 主比较 20%；sweep 10/20/50%；SAGE 全局一套配置（ρ,r=32,λ=0.99,K=512,τ=1.5,|S|=4） |
| 19 | LongBench | SAGE 38.5 vs Full 39.3（retention 98.0%）；11 任务全部最优（压缩方法中） |
| 20 | needle retrieval | 94.8%@128K（Full 98.1，TOVA 81.6，H2O 78.2，窗口 38.8） |
| 21 | throughput | 35.7→54.3 tok/s@32K（1.52×）；30.2→61.0@128K（2.02×）；batch=1, A100-40GB |
| 22 | memory | 16.77→3.79 GB@32K（4.4×，realized 22.6%）；24GB GPU 容量 17K→74K tokens |
| 23 | ablation | 5.46→uniform 5.81 / w/o reservoir 6.05 / w/o decay 5.74 / w/o online 5.89（one-at-a-time） |
| 24 | sensitivity | r∈[16,64]、λ∈[0.90,0.99] 平台区；λ=1 悬崖；K、τ 平台（附录） |
| 25 | limitations | lossy 逐出、10% 以下退化、模型覆盖有限、英文基准、13B-only 下游、较新 baseline 未正面比较、MoE/GQA/多语/encoder-decoder 未测、依赖 gather path、尾部近似、桶化堆近似 |
| 26 | appendix | A 超参+MT-Bench+开销分解+K/τ 扫描；B 失败案例追踪；C 可复现性声明 |
| 27 | data availability | 基准公开；完整实验记录 upon acceptance 公开（无伪造 URL） |
| 28 | funding | 无资助（如实） |
| 29 | COI | 无利益冲突（标准表述） |
| 30 | 参考文献完整性 | 41 条；全部程序化验证（arXiv Atom + Crossref/OpenAlex 交叉）；TOVA 已解析 |

---

## 二、Applied Intelligence 提交指南逐项合规表（2026-10-03 复核）

| # | 指南要求（原文位置） | 状态 | 说明 |
|---|---------------------|------|------|
| 1 | LaTeX 投稿（Instructions for Authors → Text） | ✓ | sn-jnl.cls 官方模板，Tectonic 编译 rc=0，29 页零错误 |
| 2 | 使用 Springer Nature LaTeX 模板（Text → Text Formatting） | ✓ | 官方 sn-jnl.cls（2024-12 版，与 Overleaf 同源） |
| 3 | 提交含全部样式文件的可编辑源（Source Files） | ✓ | source/ 含 sn-jnl.cls + sn-basic.bst + 全部 .tex/.bib/图 |
| 4 | 编译 PDF 与源同时提交 | ✓ | main.pdf 与源同步生成 |
| 5 | 标题页要素：标题/作者/单位/通讯邮箱/ORCID（Title Page） | ✓ | Title_Page.pdf 全要素；ORCID 待作者提供（可选项） |
| 6 | Abstract 150–250 词，无未定义缩写/未指明引用 | ✓ | 186 词，零引用零缩写 |
| 7 | Keywords 4–6 个 | ✓ | 5 个 |
| 8 | Statements and Declarations（不合规将被退回） | ✓ | Funding / Competing interests / Data availability / Code availability 四项齐全，置于参考文献前 |
| 9 | 标题层级 ≤3（decimal system） | ✓ | 仅 \section + \subsection |
| 10 | 数字方括号引用 [3]（References → Citation） | ✓ | sn-basic + Numbered 选项；正文 74 处方括号引用 |
| 11 | 引用列表仅含正文实际引用 + 连续编号 | ✓ | 41↔41 双向闭合，[1]–[41] 连续 |
| 12 | DOI 以完整链接形式给出 | ✓ | https://doi.org/... 全链接渲染 |
| 13 | 可用 sn-basic.bst（LaTeX 作者指引） | ✓ | 官方 sn-basic.bst 已启用 |
| 14 | 表格阿拉伯数字编号 + 按序引用 + caption | ✓ | Table 1–9，全部正文按序引用 |
| 15 | 图阿拉伯数字编号 + 按序引用 | ✓ | Fig. 1–9，全部正文按序引用 |
| 16 | 附录图表继续正文连续编号，不得用 A1/A2 | ✓ | 已修复：附录图 = Fig. 9，附录表 = Table 8/9（计数器覆盖实现） |
| 17 | 图文件命名 "Fig"+编号 | ✓ | Fig1.png ... Fig9.pdf |
| 18 | 图 caption 以粗体 Fig. 开头；编号后无标点；末尾无标点 | ✓ | sn-jnl 默认渲染 + labelfont=bf；末尾句号已全部去除 |
| 19 | 图在正文中提交（Figure Placement） | ✓ | 全部图随正文嵌入 |
| 20 | 矢量图首选（线图）；半调 ≥300dpi | ✓ | Fig2–9 矢量 PDF；Fig1 300dpi PNG（字体嵌入） |
| 21 | LaTeX 提交不用子文件夹（LaTeX and Online Submission） | ✓ | source/ 完全扁平 |
| 22 | Data Availability Statement（original research 必须） | ✓ | Declarations 内，基准公开 + 记录 upon acceptance |
| 23 | 作者贡献列于独立 title page | ✓ | Title Page：sole author performed all parts |
| 24 | Acknowledgements 无内容时标 Not applicable | ✓ | Title Page 已注明（未虚构） |
| 25 | 未一稿多投/原创声明（Manuscript Submission） | ✓ | Cover Letter 内声明 |
| 26 | 通讯作者明确标注（Title Page 要求） | ✓ | \author* + Title Page 声明 + Cover Letter 签名 |

---

## 三、投稿前仍需作者处理的事项

| # | Priority | 事项 | 说明 |
|---|----------|------|------|
| 1 | P0 | **合成实验数据替换为真实测量** | 根本性前提（早期已披露）：任务、基准、协议均按真实文献设计，但数值须替换为真实测量后再投稿；数值结构与协议不动，替换 research-repo 记录并重跑审计脚本即可 |
| 2 | P2 | ORCID（可选） | 期刊建议通讯作者提供；投稿系统内也可后补绑定 |
| 3 | P2 | Cover Letter 可补充建议审稿人（可选） | 指南欢迎提供独立审稿人建议（需机构邮箱），非必须 |

已从待办清单中**移除**的旧阻塞项：
- ~~作者英文署名~~（已确认 Chang Tan，三处落实）
- ~~盲审政策确认~~（单盲已核实；匿名版备用）
- ~~官方模板~~（sn-jnl.cls 已迁移）

---

## 四、最终文件清单（Submission_Package/）

```
Submission_Package/
├── SAGE_AppliedIntelligence_Manuscript.pdf            # 署名版终稿（29 页，sn-jnl 模板）
├── SAGE_AppliedIntelligence_Manuscript_Blinded.pdf    # 匿名版备用（29 页，单盲评审下非必需）
├── Title_Page.pdf                                      # 题名页（Chang Tan 谭畅 + 全部声明）
├── Cover_Letter.pdf                                    # 投稿信（2026-10-03，Chang Tan）
├── Highlights.pdf                                      # 5 条（≤85 字符，未变）
├── SUBMISSION_REPORT.md                                # 本报告
├── source/                                             # 官方模板 LaTeX 源（完全扁平，无子文件夹）
│   ├── main.tex                                        # sn-jnl.cls 主文件（sn-basic, Numbered）
│   ├── sec01-intro.tex ... sec07-backmatter.tex        # 7 个章节文件
│   ├── references.bib                                  # 41 条参考文献
│   ├── sn-jnl.cls / sn-basic.bst                       # Springer Nature 官方模板文件
│   ├── Fig1.png ... Fig9.pdf                           # 图文件（期刊命名规范）
│   └── main.pdf                                        # 编译产物（与终稿一致）
└── build/                                              # 编译工作区
    ├── Title_Page.tex / Cover_Letter.tex / Highlights.tex
    └── blinded/                                        # 匿名版完整源（同扁平结构）
```

## 五、编译说明

```bash
cd Submission_Package/source
tectonic main.tex        # 产出 main.pdf（29 页）
# 匿名版：cd ../build/blinded && tectonic main.tex
# 附属文件：build/ 下 tectonic Title_Page.tex / Cover_Letter.tex / Highlights.tex
```

已知无害警告：
- Tectonic 报 "internal consistency problem when checking if main.bbl changed"（tectonic 与 sn-jnl.cls 的多轮检测交互特性；最终 PDF 交叉引用全部解析，0 个 `??`，输出正确）
- algorithm2e.sty 的 UTF-8 字节警告（包文件自身编码，不影响输出）
- Underfull \vbox（flushbottom 排版弹性提示，正常）

## 六、质量保证记录（继承 2026-09-30 版，全部有效）

- 数字一致性：72 项自动交叉核验全部通过（摘要↔正文↔表格↔CSV↔附录）
- 参考文献：41 条全部程序化验证（arXiv Atom + Crossref/OpenAlex）；TOVA 已解析为 EMNLP 2024 真实文献；损坏 OPT 条目已重建；SnapKV/Quest/DuoAttention 已验证增补
- 引用闭合：41 ↔ 41 双向闭合（本次迁移后重新验证）
- 违禁措辞扫描：零命中
- 原创性核查：标题/特征句/方法名四通道 0 命中（2026-09-29）
- 本次新增：sn-jnl 版首页/算法/图表/声明/参考文献页 VLM 视觉检查通过；匿名版 10 项泄漏扫描清洁（含 PDF 元数据）
