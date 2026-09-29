#!/usr/bin/env python3
"""Repair bib entries broken by the comma-stripping regex bug."""
import re

BIB = "/home/z/my-project/paper-project/paper/references.bib"

txt = open(BIB).read()
lines = txt.split("\n")
out = []
in_entry = False
fixed = 0
for ln in lines:
    stripped = ln.strip()
    # entry opener missing comma: @type{key  (no comma)
    m = re.match(r"^@(\w+)\{([^,]+)$", stripped)
    if m and in_entry is False:
        out.append(ln + ",")
        in_entry = True
        fixed += 1
        continue
    if stripped.startswith("@") and "{" in stripped:
        in_entry = True
        out.append(ln)
        continue
    if in_entry and stripped == "}":
        in_entry = False
        out.append(ln)
        continue
    # field line missing trailing comma: field = {..}
    if in_entry and re.match(r"^\s*\w+\s*=\s*\{.*\}\s*$", ln):
        out.append(ln + ",")
        fixed += 1
        continue
    out.append(ln)

txt2 = "\n".join(out)

# a trailing comma before the final closing brace is tolerated by bibtex
# but clean it anyway: ',\n}' -> '\n}'
txt2 = re.sub(r",\s*\n\}", "\n}", txt2)

open(BIB, "w").write(txt2)
print(f"repaired {fixed} lines")

# validate: parse entries and check comma after key
entries = re.findall(r"@(\w+)\{([^,]+),", txt2)
print(f"parseable entry headers: {len(entries)}")
bad = re.findall(r"@(\w+)\{([^,\s]+)\s*\n", txt2)
print(f"still-broken openers: {len(bad)}")
