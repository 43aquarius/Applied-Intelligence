# 表达润色（英文论文）prompt 应用日志

应用对象：全部英文 LaTeX 正文（sections/*.tex，9,554 词）。

## 执行的润色动作

1. 句式优化（Gopen & Swan 七原则）
   - 主谓邻近：如 "The footprint of this cache grows linearly..."
     主语紧邻动词，无插入中断。
   - 尾重原则：每段结论性数字置于句尾（"...reaching 2.02x at 128K"）。
   - 旧信息在前：每个 \paragraph 分析先陈述结论（旧），再展开数值（新）。
   - 动词承载动作：全部 "we evaluate/trace/attribute"，仅 2 处名词化
     （"the eviction of..."，保留以避免歧义）。
2. 零错误原则
   - 冠词、拼写、标点经 scan_text_quality.py 与通读复查：
     直引号 0、缩写 0、乱码字符 0（check-tex PASS）。
3. 词汇与语体
   - 无缩写形式（it's/doesn't 全文为 0）。
   - 所有格规避："the performance of METHOD" 结构；
     未出现 METHOD's 形式。
   - 术语缩写保留：LLM/KV 不展开（术语维持约束）。
4. 结构要求
   - 严禁列表化：正文仅引言贡献 3 条 itemize（skill 规定例外），
     其余全部连贯段落 ✓。
   - 保留原格式：表格加粗为原设计（booktabs 规范），未新增任何强调。

## 修改记录（润色轮实际改动）

- 05-experiments: "the strongest uniform-budget baseline, TOVA, pays"
  （原 "the best baseline" → 具体化，符合精准原则）。
- 04-method: 拆分超长句 "The design guarantees that... and it retains..."
  为主从分明的两句。
- 06-discussion: "boring in the best sense: it is bookkeeping, not
  extrapolation"（保留——有具体含义的修辞，非空洞强调）。
- 润色判定为"保留原样"的段落：正文无 hedging 滥用（can 8 处均为
  能力陈述，见 scan 输出）。

## 结论

正文达到零语法/排版错误状态；修改阈值遵循"必要才改"（中文润色 prompt
的核心原则同样适用于英文轮的克制要求）。
