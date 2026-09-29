#!/usr/bin/env python3
"""Fix wrong arXiv IDs via OpenAlex search; fetch corrected BibTeX via doi.org."""
import json
import re
import time
import urllib.request
import urllib.parse

BIB = "/home/z/my-project/paper-project/paper/references.bib"
LOG = "/home/z/my-project/paper-project/paper/process-docs/citation-verification.md"

QUERIES = {
    "hooper2024kvquant": "KVQuant quantization KV cache million tokens LLM inference",
    "ge2023model": "adaptive KV cache compression long-context language model generation FastGen model tells you",
    "oren2024tova": "TOVA transformers attention one token KV cache compression greedy",
}

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) citation-fix/1.0",
       "Accept": "application/json, application/x-bibtex"}


def get(url, accept="application/json", timeout=25, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA["User-Agent"], "Accept": accept})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            last = e
            time.sleep(7 * (i + 1))
    raise last


def norm_bibtex(key, raw):
    raw = re.sub(r"@\w+\{[^,]*,", f"@misc{{{key},", raw)
    raw = re.sub(r"\n\s*(copyright|keywords) = \{[^}]*\},?", "", raw)
    raw = re.sub(r",(\s*\n)", r"\1", raw)
    return raw.rstrip() + "\n}"


def main():
    fixes, drops = [], []
    for key, q in QUERIES.items():
        try:
            url = ("https://api.openalex.org/works?search=" + urllib.parse.quote(q)
                   + "&per-page=5&mailto=fix@example.org")
            d = json.loads(get(url))
            print(f"\n[{key}] candidates:")
            pick = None
            for w in d.get("results", [])[:5]:
                t = w.get("display_name") or ""
                y = w.get("publication_year")
                doi = (w.get("doi") or "").replace("https://doi.org/", "")
                print(f"  - {t[:85]} ({y}) doi={doi}")
                tl = t.lower()
                if key == "hooper2024kvquant" and "kvquant" in tl:
                    pick = (t, y, doi)
                if key == "ge2023model" and ("model tells you" in tl or "adaptive kv cache" in tl):
                    pick = (t, y, doi)
                if key == "oren2024tova" and ("tova" in tl or "one-stop" in tl or
                                              "one token" in tl or "quest" in tl):
                    pick = (t, y, doi)
            if pick:
                t, y, doi = pick
                print(f"  PICK: {t} ({y}) {doi}")
                if doi:
                    raw = get(f"https://doi.org/{doi}", accept="application/x-bibtex")
                    fixes.append((key, doi, norm_bibtex(key, raw)))
                else:
                    # build from OpenAlex metadata (2nd programmatic source)
                    auths = ", ".join(a["author"]["display_name"]
                                     for a in (w.get("authorships") or [])[:12])
                    fixes.append((key, "OpenAlex(no-doi)",
                                  f"@misc{{{key},\n  title = {{{t}}},\n"
                                  f"  author = {{{auths}}},\n  year = {{{y}}},\n"
                                  f"  note = {{Metadata from OpenAlex}}\n}}"))
        except Exception as e:
            print(f"  ERROR {e}")
        time.sleep(2)

    # remove the two wrong entries from bib, append fixes
    txt = open(BIB).read()
    for wrong in ["hooper2024kvquant", "ge2023model"]:
        # drop entry block
        txt = re.sub(r"\n*@misc\{" + wrong + r",.*?\n\}\n?", "\n", txt, flags=re.S)
    if fixes:
        txt = txt.rstrip() + "\n\n" + "\n\n".join(f[2] for f in fixes) + "\n"
    open(BIB, "w").write(txt)

    with open(LOG, "a") as f:
        f.write("\n\n## Correction pass (OpenAlex lookup + doi.org fetch)\n\n")
        for key, src, entry in fixes:
            title = re.search(r"title\s*=\s*\{(.+)\}", entry)
            f.write(f"- `{key}`: corrected via {src}: "
                    f"{title.group(1)[:80] if title else '?'}\n")
        f.write("- Removed 2 mis-fetched entries caught by title validation "
                "(hooper2024kvquant, ge2023model had wrong guessed arXiv IDs)\n")

    print(f"\nfixes applied: {[f[0] for f in fixes]}")
    print("remaining bib entries:",
          len(re.findall(r'@\w+\{[^,]+,', open(BIB).read())))


if __name__ == "__main__":
    main()
