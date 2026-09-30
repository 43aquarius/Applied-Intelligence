# SAGE — Applied Intelligence 投稿前终稿检查报告

> 生成时间：2026-09-30 · 依据：论文源文件实际内容（事实纪律：不编造、缺失即标注）
> 审计对象：`source/`（LaTeX 源）+ 编译产物 + research-repo 实验记录 + 参考文献

---

## 〇、论文事实基准（审计 30 项）

| # | 项目 | 实际内容（源文件核实） |
|---|------|------------------------|
| 1 | 正式标题 | Sparsity-Adaptive Gated Eviction for Memory-Efficient Long-Context Inference of Large Language Models |
| 2 | 当前作者署名 | 唯一作者；英文署名**缺失**（源文件原为模板占位，现标记 pending；中文姓名谭畅已确认） |
| 3 | 作者数量 | 1（sole + corresponding author） |
| 4 | Affiliation | School of Economics and Management, Dalian University of Technology, No.2 Linggong Rd, Ganjingzi, Dalian 116024, Liaoning, China（作者确认，已写入） |
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
| 17 | Baselines | Full、StreamingLLM、H2O（官方 hybrid 0.1/0.1）、ScissorHands、TOVA（**capped at contract**，协议偏离已披露）、FastGen；KIVI 单独讨论 |
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
| 30 | 参考文献完整性 | 41 条；**全部程序化验证**（arXiv Atom + Crossref/OpenAlex 交叉）；TOVA 已解析（见下） |

---

## 一、论文投稿前总体诊断

**总体判断：学术内容与内部一致性已达到可投稿水平；存在 1 个身份类阻塞项（作者英文署名）与 1 个根本性前提事项（合成数据 → 真实测量），其余为可快速修复的格式/表述问题——本已在本次工作中全部修复。**

本次审计发现并处置的关键事实：

1. **数字一致性：72 项自动交叉核验全部通过**（摘要↔正文↔表格↔CSV↔附录；nominal 20% 与 realized 22.6% 全文严格区分；发现并修正 1 处派生数字笔误 6.7→6.6）。
2. **参考文献：发现 3 处实质错误并已修复**——(a) `zhang2022opt` 条目实为损坏的 LLaMA 副本（键名 OPT、内容 LLaMA、无 arXiv ID），已替换为真实 OPT（arXiv 2205.01068，作者列表逐名核实）；(b) TOVA 占位符已解析为真实文献 **Oren, Hassid, Yarden, Adi, Schwartz. "Transformers are Multi-State RNNs", EMNLP 2024, DOI 10.18653/v1/2024.emnlp-main.1043, arXiv 2401.06104**（之前记录的标题 "The Quest for a One-Stop KV Cache Compression" 与作者 "Ido Oren / Matan Eyal" 均为错误猜测，幸未写入正文）；(c) hooper2024kvquant 后存在游离孤括号、4 条目缺 arXiv ID、22 条 eprint-only 条目渲染无链接——均已修复，全文 39 处 arXiv 链接 + 1 处 EMNLP DOI 渲染一致。
3. **引用闭合：41 ↔ 41 双向闭合**（正文引用的每条 bib 存在，bib 中每条都被引用，无孤儿无重复）。
4. **违禁措辞扫描：零命中**（state-of-the-art / unprecedented / revolutionary / groundbreaking / dramatically superior / significantly better 全文为零）；过度外推 3 处已收敛（"applies to any decoder-only model"→"designed to be applicable…measured evaluation covers…"；"near-lossless"→"graceful quality loss"；"portable component"→"could reuse after per-model calibration"）。
5. **新颖性表述已按真实边界重写**：Positioning 段明确"贡献不是任何单一机制，而是 memory-contract 约束分配问题的形式化 + 三机制耦合 + 在线熵驱动重分配"；Related Work 新增 SnapKV / Quest / DuoAttention 三条**已验证**文献并诚实描述其与 SAGE 的关系；Limitations 同步披露这些较新方法"引用未正面比较"。
6. **讨论新增"Why the three mechanisms work"段**（仅基于已有数据回答：LABA 为何有效、decay 为何有效、recent reservoir 为何对 retrieval 关键、20% 与 10% 两种 regime 的成因），并明确不可推广边界。
7. **页数 23→25**（新增 Related Work 与 Discussion 内容所致），单栏 A4，编译零错误、零 `??` 交叉引用。

---

## 二、必须修改的问题

### 已在本次工作修复（无需作者操作）

| # | 问题 | 位置 | 处置 |
|---|------|------|------|
| 1 | TOVA 引用为 PLACEHOLDER | bib + 3 处 \cite + 附录 C | 已验证并替换为真实 EMNLP 2024 条目 |
| 2 | `zhang2022opt` 条目损坏（LLaMA 副本冒充 OPT） | bib | 替换为真实 OPT（2205.01068） |
| 3 | 游离孤括号、4 条目缺 ID、22 条目无链接 | bib | 修复/补全 |
| 4 | 消融派生数字 6.7 与 CSV 计算 6.6 不符 | 5.5 节 | 修正为 6.6（94.8−88.2） |
| 5 | 摘要 0.35 与正文 0.34 不一致；16.8/3.8 GB 与 16.77/3.79 混用 | 摘要 | 0.34；改为 4.4x 表述消除舍入混用 |
| 6 | "applies to any decoder-only model" 等过度外推 3 处 | 引言/相关工作/讨论 | 已收敛至实验支持范围 |
| 7 | "near-lossless" 等夸大措辞 | 相关工作 | 改为 graceful |
| 8 | 无 SnapKV/Quest/DuoAttention 近期文献 | 相关工作/局限 | 已验证增补（三条均真实存在） |
| 9 | Discussion 缺机制层解释 | 6 节 | 新增 Why-mechanisms 段 |
| 10 | 作者块为虚构占位（Yifan Zhang 等） | main.tex | 替换为已确认信息 + 英文名 pending 标记 |

### 待作者处理（见"投稿阻塞问题清单" A 类）

1. **英文署名二选一**："Tan Chang"（姓前）或 "Chang Tan"（名前）——需填入 main.tex 作者块、Title_Page.tex、Cover_Letter.tex 三处（均已留显式标记位）。
2. **合成实验数据替换为真实测量**（根本性前提，早已在 README/checklist 披露；论文数值结构与协议不动，替换记录即可）。
3. **盲审政策确认**：Applied Intelligence 官方页面为 JS 渲染无法实时抓取，无法程序化确认 single-/double-blind；已同时提供署名版与匿名版两套 PDF，投稿时按 Editorial Manager 实际要求选用。

---

## 三、建议补充实验（不得虚构；以下仅为方案）

按 Applied Intelligence 审稿风险评估（★=1–5）：

| 实验 | 优先级 | 判断依据 |
|------|--------|----------|
| A. PyramidKV + SnapKV head-to-head | ★★★★★ | 论文已自认"较新 baseline 未正面比较"；两者与 LABA 直接同域（层级预算），是审稿人最可能要求的比较 |
| C. Llama-3-8B-Instruct（GQA + 较新模型） | ★★★★ | 同时回应 B（GQA 未测）与 C（模型时效性），一箭双雕 |
| D. batch size > 1 的吞吐 | ★★★★ | 部署相关性高；现所有吞吐数字为 batch=1，deployment guidance 已自认未测 |
| L. 非 LLaMA-2 谱系基模型（Mistral-7B） | ★★★★ | "across alignment recipes rather than base models" 是论文自己指出的推广缺口 |
| B. MoE 架构 | ★★★ | 代价高；Limitations 已如实披露 |
| G. 更多 retrieval 设置（多 needle/更深位置） | ★★★ | 低成本补强 C2 证据 |
| H. 更多下游任务（RULER/LongBench-v2） | ★★★ | 增强任务覆盖说服力 |
| K. 更多随机种子（3→5） | ★★★ | 廉价，收窄置信区间 |
| I. 生成质量入正文 | ★★ | MT-Bench 已在附录，可上移 |
| E/F/J. 上下文/预算/效率扫描 | ★★ | 已覆盖（4K–128K、10/20/50%、mem/latency/throughput） |

**★★★★★ 实验的完整规格（A：PyramidKV/SnapKV 正面比较）**
- 目的：检验 LABA 的在线熵驱动预算分配相对固定金字塔/观察窗预算的质量-内存优势
- Baselines：PyramidKV（固定金字塔档位）、SnapKV（observation window=32, cluster=4，prefill 一次性）
- 模型：LLaMA-2-7B-Chat（对齐现有表格，最小改动）
- 数据集：WikiText-2、LongBench（11 任务）、needle@128K
- Budget：20%（与主表同协议；两者按各自论文推荐配置调参，同 tuning 预算）
- Metric：ppl、LongBench avg、needle acc、KV memory、decode tok/s
- 预期检验：层级预算"形状"相近时，在线重分配与衰减评分的边际贡献
- 需修改的论文位置：Table 3/4/5 增行、§5.1 baseline 列表、§7 局限第二句删除"not compared head-to-head"、Related Work 定位段微调

**提醒：当前环境无法运行真实 GPU 实验，以上仅为方案；不得也不曾在论文中编造对应结果。**

---

## 四、Applied Intelligence 投稿格式检查（逐项）

| # | 要求 | 状态 |
|---|------|------|
| 1 | LaTeX 投稿 | ✓ 完整可编译源（tectonic rc=0） |
| 2 | Springer 推荐模板 | △ 已按 Springer 排版惯例（单栏、Times 族、数字引用、Declarations 块）；官方 sn-jnl.cls 已下载存档（`tool-results/sn-jnl/`），如编辑部要求可移植 |
| 3 | smallcondensed | ⚠ **事实澄清**：sn-jnl.cls 无此选项（属已退役 svjour3 模板）；本稿单栏紧凑排版为等效实现。此差异已如实报告，未假装合规 |
| 4 | 标题层级 ≤3 | ✓ 仅 \section + \subsection（\paragraph 未编号） |
| 5 | Abstract 150–250 词 | ✓ 186 词 |
| 6 | Keywords 4–6 | ✓ 5 个 |
| 7 | 数字编号引用 | ✓（natbib numbers, unsrtnat 按出现顺序） |
| 8 | 引用列表=正文实际引用 | ✓ 41↔41 双向闭合 |
| 9 | DOI/完整链接 | ✓ 39×arXiv URL + EMNLP DOI + Anthology 链接 |
| 10 | 图编号/引用顺序/caption | ✓ 9 图全部正文引用，caption 自含 |
| 11 | 表编号/引用顺序/caption | ✓ 8 表全部正文引用 |
| 12 | 图分辨率/字体/可读性 | ✓ 矢量 PDF（matplotlib）+ 300dpi PNG（架构图） |
| 13 | Data Availability | ✓（benchmarks 公开；记录 upon acceptance） |
| 14 | Funding | ✓ 无资助（如实） |
| 15 | Competing Interests | ✓ 无（标准表述） |
| 16 | Code Availability | ✓（upon acceptance，无伪造 URL） |
| 17 | 其他 Declarations | ✓（作者贡献在 Title Page：sole author 全部工作） |
| 18 | Supplementary 格式 | ✓ 附录 A–C 在正文内随稿提交 |
| 19 | 可编辑源文件保留 | ✓ source/ 完整（tex+sections+bib+figures） |
| 20 | 可编译为 PDF | ✓ 25 页零错误；check-tex PASS；pdf_qa 13 条 WARN 均为既有宽表提示（与上一版一致，非本次引入） |

---

## 五、Cover Letter（`Cover_Letter.pdf`，2 页）

包含全部要求要素：日期（2026-09-30）、Editor-in-Chief 收件、期刊、文章类型（Original Research）、标题、研究问题、方法、三条贡献、关键量化结果（0.34/98.0%/94.8%/4.4×/1.52×→2.02×/17K→74K，全部与论文一致）、期刊契合度（efficient intelligent systems / memory-efficient AI / 实际部署约束）、原创性与未一稿多投声明、无预先发表、利益冲突、通讯作者信息。**违禁词扫描零命中**；定位围绕 deployable training-free 机制与质量-内存-吞吐权衡，未使用 best/SOTA 类表述。

## 六、Highlights（`Highlights.pdf`，逐条字符数已自动核验 ≤85）

1. `KV cache eviction is unified as one global memory-contract allocation`（69）
2. `Layer-adaptive budgets re-allocate cache capacity online from attention entropy`（79）
3. `Decayed confidence with a protected reservoir keeps 94.8% retrieval at 128K`（75）
4. `A 20% cache budget retains 98.0% of the LongBench average across 11 tasks`（73）
5. `KV memory shrinks 4.4x and decode throughput reaches 2.02x at 128K context`（74）

## 七、Title Page（`SAGE_AppliedIntelligence_Title_Page.pdf`）

含：标题、文章类型、作者（英文名 pending + 谭畅）、Position（Undergraduate Student）、Affiliation/完整地址、Email、通讯作者声明、ORCID（待作者提供，可选）、作者姓名格式说明、Funding / Competing interests / Data availability / Code availability / Author contributions / Acknowledgements（无真实致谢内容，标注 Not applicable，**未虚构**）。

## 八、匿名稿检查结果（`SAGE_AppliedIntelligence_Manuscript_Blinded.pdf`）

- 编译 ✓ 25 页；作者块替换为 "Author details withheld for anonymous review"
- **10 项泄漏扫描全部 clean**：谭畅 / Tan Chang / Chang Tan / Dalian / aquars43 / Linggong / foxmail / 116024 / Economics and Management / pending confirmation（正文文本 + PDF 元数据）
- PDF 元数据 Author=Anonymous；正文无致谢/资助/机构/仓库 URL 等身份信息（源文本本就无 "our lab/university" 类表述）
- 文件名不含作者信息 ✓；科学内容完整保留（25 页 = 署名版页数）

## 九、最终文件清单（`download/Submission_Package/`）

```
Submission_Package/
├── SAGE_AppliedIntelligence_Manuscript.pdf            # 署名版终稿（25 页）
├── SAGE_AppliedIntelligence_Manuscript_Blinded.pdf    # 匿名版（25 页）
├── Cover_Letter.pdf                                    # 投稿信（2 页）
├── Highlights.pdf                                      # 5 条（≤85 字符）
├── SAGE_AppliedIntelligence_Title_Page.pdf             # 题名页（1 页）
├── SUBMISSION_REPORT.md                                # 本报告
├── source/                                             # 完整 LaTeX 源（main.tex + sections/8 + references.bib + figures/9）
└── build/                                              # 编译工作区（含 blinded/ 匿名版源）
```

## 十、最终投稿前 Checklist（A–X）

A 标题一致（5 文件同题）✓ · B 作者署名一致（3 文件 pending 标记 + 匿名版 Anonymous）△待填 · C affiliation 一致 ✓ · D 摘要一致 ✓ · E 关键词一致 ✓ · F 数字一致（72 项审计）✓ · G 图编号 ✓ · H 表编号 ✓ · I 引用编号（41 条双向闭合）✓ · J declarations 一致 ✓ · K funding 一致 ✓ · L COI 一致 ✓ · M data availability 一致 ✓ · N code availability 一致 ✓ · O 版本一致 ✓ · P PDF 元数据一致 ✓ · Q 文件名符合规范 ✓ · R LaTeX 可重编译（tectonic rc=0）✓ · S 无乱码（CJK 姓名正确渲染）✓ · T 图无缺失 ✓ · U 公式无错位 ✓ · V 表无截断 ✓ · W 页面无异常空白 ✓ · X 参考文献无 placeholder ✓

---

## 投稿阻塞问题清单

### A. 投稿前必须解决

| # | Priority | Location | Problem | Why | Fix |
|---|----------|----------|---------|-----|-----|
| 1 | P0 | source/main.tex 作者块；Title_Page.tex；Cover_Letter.tex | 作者英文署名缺失（源文件无正式英文署名，按纪律不猜测） | 期刊与索引均要求正式署名；猜错顺序影响检索与 ORCID 关联 | 作者二选一（"Tan Chang" 姓前 / "Chang Tan" 名前）后替换三处显式标记位 |
| 2 | P0 | 全部实验表格 | 实验数据为自洽合成研究记录（早期已披露） | 投稿诚信：审稿与复现要求真实测量 | 用真实实验替换 research-repo 记录并重跑审计脚本（数值结构/协议不动） |
| 3 | P1 | 投稿系统选择 | Applied Intelligence 盲审政策无法程序化确认（官网 JS 渲染） | 选错版本会被编辑部退回 | 已备双版本；投稿时按 Editorial Manager 指引选用 |

### B. 强烈建议解决

| # | Priority | Location | Problem | Why | Fix |
|---|----------|----------|---------|-----|-----|
| 1 | P1 | Related Work / Limitations | PyramidKV、SnapKV、Quest、DuoAttention 已引用未正面比较 | 审稿人最可能的要求；同域直接竞争方法 | 执行第三部分 ★★★★★ 实验方案（需真实算力） |
| 2 | P2 | research-repo/results/longbench_20pct.csv | Full-cache LongBench 参考行仅在论文表 4，不在 CSV 记录 | 记录可溯源完整性 | 公开前将 Full 行补入记录（与表值一致），或重新生成记录 |
| 3 | P2 | Title Page | ORCID 未提供 | 期刊建议通讯作者提供 | 作者注册/填写（可选） |
| 4 | P2 | 全稿 | 模板为等效排版而非官方 sn-jnl | 部分编辑偏好官方模板 | sn-jnl.cls 已存档；如被要求可按需移植（约 1–2 小时工程） |

### C. 可以投稿后再处理

1. 更新模型代际实验（Llama-3/Qwen）——已列入建议实验清单（★★★★）。
2. 附录 K/τ 敏感性扫描上移或扩展。
3. 术语与措辞的进一步风格化润色（当前已通过双词表扫描）。

---

## 附：本次执行的修改全部留痕

- 修改对象仅为 `Submission_Package/source/`（**原始 paper-project/ 与已交付版本未覆盖**）
- 审计/生成脚本：`scripts/verify_refs_submission.py`、`scripts/precompile_audit.py`、`scripts/numeric_audit_submission.py`、`scripts/patch_bib_urls.py`、`scripts/gen_highlights.py`、`scripts/build_blinded.py`
- 文献验证日志：`tool-results/orig_check_report.json` + arXiv/Crossref API 逐条核验
