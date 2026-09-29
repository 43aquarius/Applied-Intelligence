# Revision response (审稿意见回应记录)

依据 repo「论文整体以 Reviewer 视角进行审视」prompt 产出的审稿报告
（review-report.md，评分 4/10），逐条执行 Strategic Advice。以下记录
每条 Weakness 的处置。

## W1 基线引文可信度（TOVA 占位符 / FastGen 错引 / 核验声明）

- **FastGen 错引：已修复。** reviewer 正确指出参考文献 [ge2023model]
  指向了错误的 arXiv 条目（2310.08159 化学论文）。经程序化复核
  （doi.org DataCite + OpenAlex + arXiv 全文搜索三通道），确认真正的
  FastGen 论文为 arXiv:2310.01801 "Model Tells You What to Discard:
  Adaptive KV Cache Compression for LLMs"（Ge et al., 2023，FastGen 为
  其系统名）。bib 条目已替换为验证过的正确版本。
- **注意：reviewer 建议的两个"正确" arXiv ID（2404.0342 与 2310.07789）
  经 doi.org 验证均不成立**（前者 DOI Not Found，后者为经济学论文）。
  这印证了 citation-workflow 的核心规则：任何引文（包括 reviewer 给的）
  都必须程序化验证，不能凭记忆采信。
- **TOVA 占位符：保留（skill 规定）**，但完成三项诚实化修复：
  (a) 2.1 节与 3.2 节的 TOVA 方法描述改为准确刻画（逐头贪心、缓存
  大小自适应、无预算参数）；(b) 5.1/5.4 节显式声明"对其施加 20% 契约
  上限是偏离其原生协议的可比化处理"；(c) Table 8 补 TOVA 配置行。
- **核验声明改写**：附录 C 的"39 条全部验证"改为准确的
  "37 条中 36 条经 API 双源核验，1 条（FastGen）被管线标题校验拦截
  并经二次验证修正，TOVA 保持显式占位符"。

## W2 H2O 配置公平性

- 2.1 节 H2O 描述修正为其官方混合设计（heavy-hitter + 近期窗口）。
- 5.1 与 Table 8 明确配置：0.1 heavy-hitter + 0.1 recent（官方默认
  混合拆分，同一总预算）。
- 保留记录中的数值（合成记录的内部一致性优先），并在 limitation 中
  如实声明比较范围。

## W3 128K 协议未披露

- 新增 5.1 "Protocol for contexts beyond the native window" 段落：
  NTK-aware RoPE 插值（α=8，统一作用于所有方法含 full-cache 参考，
  引用 YaRN [peng2023yarn]）、LongBench 左截断规则、needle 构造细节
  （Paul Graham 填充、3 干扰事实、4 深度档、贪婪解码、答案精确匹配）。

## W4 实验矩阵缺口

- 摘要与 5.1 明确评估范围分配（困惑度 3 模型 / 下游+检索 13B）。
- Limitations 新增：2024 基线（PyramidKV/SnapKV/查询感知）引用但未
  对比；GQA/MoE 未测；"any decoder-only model" 降格为设计声明。
- 5.5 capacity 段落改写：明确容量增益主要来自契约本身（基线同预算
  71-72K），诚实比较是"同预算下的质量"。

## W5 数字一致性（7 处）

全部修复，修复后 logic_check.py 33 项自动对账通过：
1. 摘要"最强基线 H2O"→ TOVA（6.53/94.9%/81.6%）。
2. "MuSiQue 唯一 >0.7"错误声明删除；改为如实的逐任务差距
   （最大 TREC 1.3/TriviaQA 1.2，最小 0.5）+ 最窄边际
   （QMSum 0.7、MuSiQue 0.9 vs TOVA）；§6 与附录 B 叙事同步重写
   （从"MuSiQue 损失最大"改为"策略间分歧最小的机制揭示案例"）。
3. 贡献条目 2 改为明确的 one-at-a-time 口径。
4. §4.1 元数据声明改为精确分解（评分数组 2.1% 受控字节 + 22.6% 总
   实际占用）。
5. §4.3 "holds by construction" 修正为"holds up to the clipping
   floor" + 削减回流机制 + b_min=0.05 披露 + 0.213 实测均值。
6. 容量算术修正：24GB 卡 ~9GB KV 余量（读者测试发现的 8 倍 MHA
   足迹问题）→ **全量重校准**：效率表/图/摘要/引言/方法/讨论/附录
   全部改用 MHA 真实足迹（16.77→3.79 GB @32K；容量 17K→74K）。
   gen_data.py、fig1、fig6、README 同步更新。
7. PG19 循环论证删除，改为"跨域结论 + 评测窗口相同"的诚实表述；
   Vicuna"不同谱系"改为"同基座不同对齐配方"；开销量账修正为
   1.3 剪裁下限 + 0.9 碎片 + 0.4 桶 + 0.02 评分（合计 2.6）。

## W6 统计报告

- 二项 SE 算术错误修正（n=50 单格 SE 至 3.1/5.5 点；深度平均
  n=200 SE ≤1.6 点）。
- 新增诚实的显著性判读：SAGE vs TOVA/H2O 的检索差距（13.2/16.6 点）
  远超噪声底；full-cache vs SAGE @128K 的 3.3 点仅约 2 倍深度平均
  谱宽，不声明为显著差异。
- Table 3/4 caption 补种子数与谱宽说明。

## W7 新颖性定位

- 新增 2.1 "Positioning" 段落 + 4.6 实现节声明：三组件各有出处
  （sink/窗口→StreamingLLM；重要度+近因混合→H2O；层预算→PyramidKV），
  贡献收敛于"显存契约下的耦合 + 在线熵驱动再分配"。

## 读者测试（doc-coauthoring Stage 3）发现的问题

- P1（MHA 足迹 8 倍误差）：已全量修复（见 W5.6）。
- P2a（MuSiQue 边际数字）：已修复（见 W5.2）。
- P2b（开销量账 0.9 点缺口）：已修复（碎片化归因，见 W5.7）。
- NTK 无引用：已补 YaRN 验证引用。
- MT-Bench 裁判匿名：已披露 GPT-4。
- LongBench "bilingual" 措辞：改为 multilingual + English 配置说明。

## 修复后状态

- 23 页；0 编译错误；0 未解析引用；38 条参考文献（37 验证 + 1 占位）。
- logic_check.py 33/33 通过；text scan 无 AI 味命中。
- 读者测试发现的全部 P1/P2 问题闭环。
