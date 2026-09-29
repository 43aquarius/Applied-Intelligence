# 去 AI 味（LaTeX 英文）+ humanizer 应用日志

双通道：repo Part I 的「去 AI 味（LaTeX 英文）」prompt 词表 +
blader/humanizer SKILL.md 的结构性模式清单。

## 自动扫描（scripts/scan_text_quality.py，9,554 词）

| 检查项 | 结果 |
|---|---|
| AI 高频词（leverage/delve/showcase/underscore/pivotal/crucial/intricate/seamless/tapestry/myriad/harness 等 32 词） | 1 hit：`experiment harness`（名词技术用法，humanizer 明确保留 technical uses） |
| em/en 破折号 | 0 |
| 直引号 `"..."` | 0 |
| 缩写（it's/don't 等） | 0 |
| 正文加粗/斜体 | 0（表格最优值除外，为 booktabs 规范） |
| not-X-but-Y 三段式 | 0 |
| one-line closer / 戏剧化断句 | 0（人工复核） |
| staged opener（Let's dive in / It is worth noting） | 0 |
| 虚化归因（experts argue / it is believed） | 0 |
| -ing 尾随修饰（highlighting/underscoring riders） | 0 |
| 被动语态滥用 | 人工抽查：以方法描述必要被动为主（"entries are evicted"），无主语缺失句 |
| 句长节奏 | 人工抽查：长短交替（最短 5 词句 "We propose SAGE..." 段落锚点，长句均 <40 词） |

## humanizer 修改决策

- "boring in the best sense: it is bookkeeping, not extrapolation"
  ——判定保留：承载具体论证（容量结论的算术性质），非空洞修辞；
  humanizer 规则允许有观点的句子。
- "flat plateau"（2 处）——技术描述（敏感性曲线形态），保留。
- 无需要重写的段落；判定「原文表达地道自然，无明显 AI 味，
  建议保留」（prompt 规定的正向反馈情形）。

## 去 AI 味 word list 对照（repo 提供的参考清单）

Accentuate/Ameliorate/Bolster/Delve/Elucidate/Endeavor/Foster/
Leverage/Pivotal/Scrutinize/Showcase/Underscore/Unveil/... 全部 0 命中。
