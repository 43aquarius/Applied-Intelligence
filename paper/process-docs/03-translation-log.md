# 中转英-latex 应用日志 (Part I prompt: 中转英-latex)

每章流程：中文草稿（process-docs/drafts_zh/）→ 应用「中转英-latex」prompt →
输出 Part 1 [LaTeX]（英文正文）+ Part 2 [Translation]（回译核对）。

## 执行约束（每节均执行自查）

- 特殊字符转义：`%` → `\%`，模型名下划线避免出现于正文；公式保留 `$`。
- 时态统一：方法与实验结论用一般现在时；无历史叙述需要过去时。
- 视觉约束：正文无 `\textbf`/`\emph`（表格内最优值加粗除外，属表格规范）；
  无破折号；引言贡献列表为 skill 规定的标准例外（ml-paper-writing 要求
  2-4 条贡献列表）。
- 段落连贯：拒绝 `\item` 列表（除贡献列表外），全部连贯段落表达。
- 术语表：SAGE、KV cache、confidence score、eviction、budget、reservoir、
  retention、recent window、sink tokens、layer-adaptive —— 全文唯一译名。

## 逐节回译核对记录

| 节 | 中文草稿 | 英文化要点 | 回译一致性 |
|---|---|---|---|
| Abstract | 5 句式（Farquhar）：成就→难点→方法→证据→最亮点数字 | "免训练"→training-free；三机制命名 ACS/LABA/DRE | 数字与草稿一致（5.46/5.12/8.09/98.0%/94.8%/1.52x/2.02x/39K→168K） |
| 1 Introduction | 失效模式三段式 + 贡献三条 | "统一预算"→uniform per-layer budget；"陈旧性"→staleness | 0.69→0.34 与 0.28 与消融表核对一致 |
| 2 Related work | 按方法学组织（逐出/量化/稀疏注意力/评估），非逐篇 | "叠加"→stacked/orthogonal dimensions | TOVA 引用因无法程序化验证改为 PLACEHOLDER 键（skill 规定） |
| 3 Preliminaries | 契约式 (1)、三失效模式可操作化 | "显存契约"→memory contract | 公式与 4 节引用闭合 |
| 4 Method | ACS (2)、κ (3)、预算 (4)、逐出 (5)、算法 1 | "分桶最小堆"→bucketed minimum heap | 复杂度声明（0.1% 元数据、O(1) 均摊）与 4.6 实现一致 |
| 5 Experiments | \paragraph{结论} + 数值分析（实验分析 prompt 结构） | 每个实验先声明支撑的 claim | 全部数值与 CSV 一致（logic_check.py 33 项核对通过） |
| 6-8 讨论/局限/结论 | 失败案例机制 + 部署建议 | "甜点区"→flat plateau | MT-Bench/τ/K 附录数据一致 |

## 审稿人视角自查（prompt 的 Execution Protocol）

- 无未翻译中文残留 ✓（grep 中文全文字符=0）
- 无过度排版：正文无加粗斜体 ✓
- 逻辑跳跃：由 logic_check 的 33 项数值一致性核对替代人工 ✓
