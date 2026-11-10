# Related-work update — 2026-11-10（重建版）

> 原版在沙箱回收中丢失，本文件为依据重新核实结果重建（所有 arXiv 元数据已逐条
> 打开摘要页二次核实，非搜索片段转述）。本文件同时是 sec2_related.tex 补丁的
> 完整说明，补丁正文已应用到 repo/paper/。

## 一、P0 发现：SAGE-KV 同名冲突（必须处理）

- **SAGE-KV** = "LLMs Know What to Drop: Self-Attention Guided KV Cache Eviction
  for Efficient Long-Context Inference"，Guangtao Wang, Shubhangi Upasani, Chen Wu,
  Darshan Gandhi, Jonathan Li, Changran Hu, Bo Li, Urmish Thakker，
  arXiv:2503.08879（2025-03-11 v1）。
- 方法：prefill 后一次性 token+head 级 top-k 选择（Self-Attention Guided Eviction）。
- **与我方 SAGE（Sparsity-Adaptive Gated Eviction）无任何关系**，仅缩写相同。
- 审稿人几乎必查；不主动消歧会被认为回避。**处理**：相关工作 "Query-aware and
  prefill-time selection" 段落显式引用 + 脚注说明（保留缩写以维持与已发布代码/
  日志的连续性；冲突是时间巧合而非同源）。不建议改名：改名破坏 artifact 连续性，
  且我方 v2 已以 SAGE 名义发布 Release。

## 二、P1：Ada-KV 最近前作（必引 + 差异化）

- **Ada-KV** = "Ada-KV: Optimizing KV Cache Eviction by Adaptive Budget Allocation
  for Efficient LLM Inference"，Yuan Feng, Junlin Lv, Yukun Cao, Xike Xie,
  S. Kevin Zhou，**NeurIPS 2025**，arXiv:2407.11550（v5 2025-10-16）。
- 内容：建立 pre-/post-eviction 注意力输出的理论损失上界，解释既有方法的优化
  目标；据此提出**首个 head-wise 自适应预算分配**（层内跨 head 全局 top-k 分配，
  prefill 后一次性；防饿死超参 α=0.2）。
- **差异化表述（已入正文）**：单位不同（layer vs head）；保证不同（每步解码刷新、
  定理 1 精确整数契约 vs 事后损失界）；时机不同（online vs post-prefill）。
- **新颖性结论：完好**。Ada-KV 证明"自适应预算"是活跃方向，反而支撑我方 RQ3/RQ4
  叙事（allocation 是 first-class 设计轴）；我方贡献是预算本身的精确契约与在线化。

## 三、2025-2026 近期工作（一句带过式引用，全部已核实）

| key | 论文 | arXiv | 一句话 |
|---|---|---|---|
| ni2025refreekv | ReFreeKV: Towards Threshold-Free KV Cache Compression（Ni, Xu, Lyu, Wang, Yu, Liu, Meng, Zhou, Li） | 2502.16886 | 无阈值自适应预算调整，保持 full-cache 性能 |
| roy2026kvec | Coverage-Driven KV Cache Eviction…（Roy, Zhai, Hajimirsadeghi, Samei） | 2606.29563 | coverage 驱动，跨 head/跨层覆盖模块；方法名 **K-VEC** |
| yang2026indexmem | IndexMem: Learned KV-Cache Eviction with Latent Memory…（Yang, Gu, Xu, Li, Liu, Liu, Zhu, Guo, Han） | 2605.25475 | 可学习 indexer 预测重要性 + 潜在记忆补偿态 |
| dong2026foresightkv | ForesightKV: … by Learning Long-Term Contribution（Dong, Liu, Li, Chen, Peng, Wang, Zhao） | 2602.03203 | 训练式框架，学习预测长文本生成中的驱逐 |
| mai2026laprox | Reformulating KV Cache Eviction Problem…（Mai, Kim） | 2605.07234 | LaProx：输出感知、逐层矩阵化重构，显式建模注意力×值投影交互 |

**纠正记录**：前轮曾把 arXiv:2606.29563 记为 "ChampionKV"；本轮打开摘要页核实
实际方法名为 **K-VEC**（Coverage-Driven），bib 键相应改为 roy2026kvec。
另一纠正（前轮已纠）：arXiv:2502.16886 是 ReFreeKV，不是 DBudgetKV。

## 四、共同缺口（我方定位句）

以上近作无一提供**已实现全局预算的精确整数契约**——这正是 SAGE 的目标缺口
（补丁末句已点明）。

## 五、补丁应用状态

- references.bib：追加 7 条（bib_additions.bib），键无冲突（原 21 条不含以上键）。
- sec2_related.tex：3 处编辑（Ada-KV 插入句 / 近作扩展句+缺口句 / SAGE-KV 消歧句）。
- sec2_related.tex 附带修正：范围声明 "(models to 0.5B, contexts to 4K, CPU)"
  → "(models to 3B, contexts to 4K, CPU plus a single-T4 GPU replication)"，
  与 RQ7 一致（原句在 GPU 章节加入后已过时）。
- sec7_discussion.tex：新增 "Choosing the dials in practice." 段（γ/τ 实操指南）。
