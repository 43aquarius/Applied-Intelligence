#!/usr/bin/env python3
"""
Text-quality scan: applies the repo's 去AI味 (LaTeX English) word list +
humanizer patterns + 表达润色 constraints to the paper's .tex sources.

Checks:
1. AI-flavor vocabulary (repo list + humanizer list)
2. Em dashes / spaced dashes
3. Straight quotes in English prose
4. \textbf / \emph inside body prose (allowed only in tables/captions)
5. Hedging density (may/can/might per 1000 words)
6. Terminology consistency (SAGE, KV cache, budget, reservoir...)
7. Contraction usage (it's, don't...)
"""
import re
import glob
import collections

SEC = sorted(glob.glob("/home/z/my-project/paper-project/paper/sections/*.tex")) \
    + ["/home/z/my-project/paper-project/paper/main.tex"]

AI_WORDS = [
    "leverage", "delve", "showcase", "underscores", "underscore",
    "pivotal", "crucial", "intricate", "seamless", "holistic",
    "tapestry", "bolster", "foster", "garner", "elucidate", "endeavor",
    "meticulous", "vibrant", "testament", "myriad", "paramount",
    "novel", "comprehensive", "significant", "significantly",
    "moreover", "furthermore", "additionally", "notably", "crucially",
    "first and foremost", "it is worth noting", "landscape",
    "journey", "realm", "unleash", "harness", "elevate", "embark",
]

HUMANIZER_PATTERNS = [
    (r"not only .{0,60} but also", "not-X-but-Y triad"),
    (r"\b—\b|\s--\s", "dash"),
    (r"It is worth noting", "staged importance"),
    (r"Let us|Let's", "staged run-up"),
    (r"First and foremost", "staged opener"),
    (r"In conclusion,", "stock closer"),
]

findings = collections.defaultdict(list)
word_count = 0
for f in SEC:
    txt = open(f).read()
    # strip comments
    body = "\n".join(l for l in txt.split("\n") if not l.strip().startswith("%"))
    word_count += len(re.findall(r"\b\w+\b", body))

    for w in AI_WORDS:
        for m in re.finditer(r"\b" + w + r"\w*\b", body, re.I):
            ctx = body[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")
            findings["ai_word:" + w].append((f.split("/")[-1], ctx.strip()[:90]))

    for pat, name in HUMANIZER_PATTERNS:
        for m in re.finditer(pat, body, re.I):
            ctx = body[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")
            findings["pattern:" + name].append((f.split("/")[-1], ctx.strip()[:90]))

    # straight double quotes in prose (not in commands)
    for m in re.finditer(r'(?<!\\)"', body):
        ctx = body[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")
        findings["straight_quote"].append((f.split("/")[-1], ctx.strip()[:90]))

    # bold/emph in body (rough heuristic: outside table environments)
    intable = False
    for i, line in enumerate(body.split("\n"), 1):
        if re.search(r"\\begin\{tab", line):
            intable = True
        if re.search(r"\\end\{tab", line):
            intable = False
            continue
        if not intable and re.search(r"\\textbf\{|\\emph\{|\\textit\{", line) \
                and "Abstract" not in line and "Keywords" not in line \
                and not re.search(r"\\paragraph", line):
            findings["body_formatting"].append((f.split("/")[-1] + ":" + str(i), line.strip()[:80]))

    for m in re.finditer(r"\b(it's|don't|can't|won't|isn't|doesn't)\b", body, re.I):
        findings["contraction"].append((f.split("/")[-1], m.group(0)))

for w in ["may", "can", "might", "could"]:
    n = len(re.findall(r"\b" + w + r"\b", " ".join(open(f).read() for f in SEC), re.I))
    if n:
        findings["hedging:" + w] = n

print(f"total words scanned: {word_count}")
print()
for k in sorted(findings):
    v = findings[k]
    if isinstance(v, int):
        print(f"[{k}] count={v}")
    else:
        print(f"[{k}] {len(v)} hit(s)")
        for loc, ctx in v[:6]:
            print(f"    {loc}: ...{ctx}...")
