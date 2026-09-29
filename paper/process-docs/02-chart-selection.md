# Experiment plotting recommendation (实验绘图推荐 prompt applied)

Role: data-visualization expert for top venues. Chart types selected from
the standard academic chart library (19 types) in the repo prompt, applied
to each experiment in notes/experiment-plan.md.

## E1 Perplexity vs KV budget (ppl_compression.csv)

1. 推荐方案：带置信区域的折线图（line plot with confidence bands, chart #6）
2. 核心理由：budget 是连续控制变量（0.1-1.0），折线揭示退化趋势与拐点；
   半透明阴影表达 3 个种子的标准差，体现统计严谨性。SAGE 与基线的差距
   在 0.1-0.2 段最直观。
3. 视觉设计规范：
   - X 轴：KV budget（fraction of full cache），对数刻度，0.1/0.2/0.5/1.0。
   - Y 轴：perplexity（WikiText-2 / PG19 两面板）。
   - 统计要素：mean 实线 + ±1 std 阴影带（标注 std 语义）。
   - 配色：Ocean Dusk 调色板；SAGE 用珊瑚色 #E76F51 突出，基线用灰蓝递减；
     辅以不同 marker（o/s/^/D）保证灰度可读。

## E7 Layer-wise budget profile (layer_budget.csv)

1. 推荐方案：纵向柱状图（chart #1）+ uniform 基准虚线
2. 核心理由：32 层的 retention ratio 是离散分布，柱状最直观呈现
   "深层更稀疏"的漏斗形状；0.20 虚线显示均匀预算的浪费。
3. 视觉设计规范：X=layer index(1-32)，Y=retention ratio；柱色单一
   （低饱和蓝），虚线灰色；无误差棒（确定性的调度输出）。

## E2 LongBench per-task (longbench_20pct.csv)

1. 推荐方案：雷达图（chart #4）
2. 核心理由：11 个任务的多维综合评估，雷达图在一张图内对比 5 个方法的
   保留轮廓，证明"无短板"；配合表格给出精确数值。
3. 视觉设计规范：11 轴（任务名缩写），Full 用浅灰填充为参考轮廓，
   SAGE 珊瑚色实线；单次评估每任务，不加误差棒（表中报告 std）。

## E3 Needle retrieval (needle_heatmap.csv)

1. 推荐方案：热力图（chart #11），SAGE vs H2O 双面板
2. 核心理由：检索精度由 (深度 × 上下文长度) 二维矩阵构成，热力图能同时
   显示"深度盲区"与"长度衰减"两种失效模式；H2O 的右下角退化与 SAGE 的
   平坦高原形成最强对比。
3. 视觉设计规范：X=context length (8K-128K)，Y=document depth (4 bins)；
   colormap: YlOrRd 反转（绿=好）；单元格标注数值；colorbar 收缩。

## E4 Efficiency (efficiency.csv)

1. 推荐方案：双面板折线图（chart #6 变体）：(a) KV memory vs context；
   (b) decode throughput vs context
2. 核心理由：两条效率曲线共享 X 轴（context length），左右面板分别回答
   "省多少显存"与"快多少"；吞吐图可标注 speedup 倍数。
3. 视觉设计规范：X=context length (4K-128K)；(a) Y=KV memory (GB)：
   Full 蓝灰实线 vs SAGE 珊瑚实线，标注 4.4x；(b) Y=tokens/s：
   同配色 + 末端标注 1.52x/2.02x。

## E5 Ablation (ablation.csv)

1. 推荐方案：横向条形图（chart #2）双面板（ppl 与 LongBench avg）
2. 核心理由：消融配置名称长（"w/o layer-adaptive budgets..."），
   横向条形避免 X 轴文字倾斜；SAGE(full) 用珊瑚色，变体用灰蓝。
3. 视觉设计规范：Y=configuration，X=metric value；虚线标注 Full-cache
   基准（5.12 / 39.3）；数值标注在条末端。

## E6 Sensitivity (sensitivity_*.csv)

1. 推荐方案：双 Y 轴折线图（chart #17）
2. 核心理由：reservoir size r 与 decay λ 各有一个"甜点区"，双 Y 轴
   （左 ppl、右 needle@128K）同时显示两个指标对同一超参的响应，
   直接支撑论文的默认配置选择。
3. 视觉设计规范：X=hyperparameter（对数刻度 for r）；左轴 ppl（蓝实线），
   右轴 needle（珊瑚虚线+方 marker）；标注默认值竖虚线。

## 颜色与可访问性

- 调色板：Ocean Dusk（#264653/#2A9D8F/#E9C46A/#F4A261/#E76F51）+
  灰色基线 #B0BEC5；色盲安全组合，辅以 marker/线型区分（灰度可读）。
- SAGE 一律使用 #E76F51 珊瑚色高亮；基线共享灰蓝系。
- 图内不放置标题（caption 承担说明职能，符合顶会规范）；轴标签与刻度
  使用英文（论文语言为英文）。
