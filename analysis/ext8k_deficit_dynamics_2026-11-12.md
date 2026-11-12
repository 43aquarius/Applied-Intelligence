# ext8k Under-Retention Deficit Dynamics — 逐亏欠事件分析（Task 21, 2026-11-12）

> 数据：`repo/results/gpu/ext8k/ppl/*.accounting.json`（matched-entry fp32, rho=0.2,
> Qwen2.5-1.5B, chunk=64）。图：`fig_ext8k_deficit.png`。脚本：
> `scripts/ext8k_deficit_dynamics.py`。本文档定位：RQ7b honest-reporting 段的
> rebuttal 素材与附录图候选。

## 1. 汇总表（机器生成，2026-11-12）

| policy | steps | deficit steps | onset t | max deficit | max deficit / nominal (per-step) |
|---|---|---|---|---|---|
| 8K adaptive | 128 | 4 | 5,888 | 13 | 0.029% (t=8,000) |
| 16K adaptive | 256 | 57 | 5,888 | 100 | **0.185%** (t≈9,664) |
| 16K uniform | 256 | 0 | -- | 0 | -- |
| 16K h2o | 256 | 0 | -- | 0 | -- |
| 16K pyramidkv | 256 | 0 | -- | 0 | -- |

预算轨迹：B(t) = rho · n_layers · t = 5.6 entries/step（28 层 × 0.2）；补给固定
64 entries/step；B(t_onset) = 32,972。**8K/16K onset 同为 t=5,888**：两窗的 B(t)
轨迹与 κ-EMA 驱动的权重漂移在 t<8,192 完全相同（同一 prefill 流），机制自洽的
直接证据——亏欠起点不是窗口属性的函数，而是预算规模 B(t) 与累积权重漂移的函数。

## 2. 逐事件结构（16K adaptive，共 23 个亏欠事件，前 12 列出）

| ep | t 区间 | 步数 | max deficit |
|---|---|---|---|
| 1 | 5,888 | 1 | 2 |
| 2 | 6,720 | 1 | 1 |
| 3 | 7,424 | 1 | 4 |
| 4 | 8,000 | 1 | 13 |
| 5 | 8,832 | 1 | 28 |
| 6 | 9,088-9,152 | 2 | 24 |
| 7 | 9,664-10,112 | 8 | **100** |
| 8 | 10,368 | 1 | 3 |
| 9 | 10,752 | 1 | 4 |
| 10 | 11,136 | 1 | 18 |
| 11 | 11,456-11,648 | 4 | 33 |
| 12 | 12,096 | 1 | 16 |

结构特征：
- **事件化而非持续**：57 个亏欠步聚成 23 个短事件（多数 1 步，最长 8 步），
  事件间 cache 追平预算——自愈的直接可视化。
- **最长事件 ep7**（8 步, t 9,664-10,112, max 100）之后立即恢复，且其后仍有
  16 个零散小事件，幅度（3-33）低于 ep7——与"κ-EMA 漂移 + 64/步回填"的
  赛跑动态一致：漂移是间歇脉冲，回填速率恒定。
- 单步事件回填即愈（64 ≥ deficit）；多步事件 = 预算连续多步跑赢回填。

## 3. 口径发现（重要 — 已触发论文修订）

论文 v2.3 sec6 原句 "$\le 0.03\%$ and $\le 0.11\%$ of the nominal budget" 的分母
是**窗口末满额预算**（8K: 13/45,875 = 0.028%；16K: 100/91,750 = 0.109%）。
若按最自然的读法——亏欠发生那一步的名义预算——16K 为
**100 / 54,118 = 0.185% ≈ 0.19%**（t≈9,664 处 B(t)=5.6×9,664）。8K 两口径几乎
一致（deficit 峰值 t=8,000 已近窗口末），16K 相差 1.7×。

**处置**：论文修订为 per-step 口径（0.19%），更保守、防审稿人复算；Reviewer
Prep Q9 同步。修订后句子见 `sec6_experiments.tex` RQ7b honest-reporting 段。
（若修订版未及投稿，以修订版为准；0.11% 并非虚假——满额口径下成立——但
per-step 口径更无懈可击。）

## 4. Rebuttal 用途建议

- **附录图候选**：fig_ext8k_deficit.png (a) 面板展示 one-sided / bounded /
  policy-specific 三性质 + 对照组贴零线；(b) 面板展示相对幅度 <0.19%。
- **标准答复链**（审稿人若问"under-retention 是否破坏契约"）：
  1. 契约是上界，任何步任何 run 从未超（over-fill=0 全局）；
  2. projector 无罪（10^5 随机实例零失败，Task 18 审计）；
  3. 亏欠有界（≤0.19% of that step's nominal）、单侧、事件化自愈（本笔记 §2）；
  4. sage-uniform 在双窗 PPL 最优且 floor-exact —— 部署级 tiebreaker。
- **onset=5,888 双窗一致性**（§1）可作"机制而非巧合"的一句证据。

## 5. 机器可复现

```
python3 scripts/ext8k_deficit_dynamics.py   # 表 + 图 + 非空白校验
```
所有数字直接读自 accounting JSON 的 steps[]（t, total_retained, nominal_budget）。
