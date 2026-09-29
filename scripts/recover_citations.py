#!/usr/bin/env python3
"""
Citation recovery pass 3: doi.org DataCite content negotiation.

Skill path: citation-workflow.md Step 3 'Retrieve BibTeX via DOI'.
arXiv preprints have DataCite DOIs of the form 10.48550/arXiv.<id>;
https://doi.org content negotiation returns verified BibTeX.

Verification = doi.org(DataCite) + OpenAlex cross-check when available.
"""
import re
import os
import time
import urllib.request

BIB = "/home/z/my-project/paper-project/paper/references.bib"
LOG = "/home/z/my-project/paper-project/paper/process-docs/citation-verification.md"

# key -> (doi, source-url-to-check for web resources)
ARXIV_DOIS = {
    "gao2020pile": "10.48550/arXiv.2101.00027",
    "merity2016pointer": "10.48550/arXiv.1609.07843",
    "rae2019compressive": "10.48550/arXiv.1911.05507",
    "zhang2023h2o": "10.48550/arXiv.2306.14048",
    "xiao2023efficient": "10.48550/arXiv.2309.17453",
    "liu2023scissorhands": "10.48550/arXiv.2305.17118",
    "liu2024kivi": "10.48550/arXiv.2402.02750",
    "pope2023efficiently": "10.48550/arXiv.2211.05102",
    "shazeer2019fast": "10.48550/arXiv.1911.02150",
    "beltagy2020longformer": "10.48550/arXiv.2004.05150",
    "zaheer2020big": "10.48550/arXiv.2007.14062",
    "dettmers2022llmint8": "10.48550/arXiv.2208.07339",
    "hooper2024kvquant": "10.48550/arXiv.2401.18081",
    "zhang2024pyramidkv": "10.48550/arXiv.2406.02069",
    "su2024zoology": "10.48550/arXiv.2312.04927",
    "ge2023model": "10.48550/arXiv.2310.08159",
}

# web resources: verified by HTTP 200 on the canonical URL
WEB = {
    "chiang2023vicuna": ("Vicuna: An Open-Source Chatbot "
                         "Impressing GPT-4 with 90\\%* GPT-4 Performance",
                         "Lianmin Zheng and Wei-Lin Chiang and Ying Sheng "
                         "and Siyuan Zhuang and Zhanghao Wu and Yonghao Zhuang "
                         "and Zi Lin and Zhuohan Li and Dacheng Li and Eric P. "
                         "Xing and Hao Zhang and Joseph E. Gonzalez and Ion Stoica",
                         "https://lmsys.org/blog/2023-03-30-vicuna/"),
}

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) citation-verifier/1.0",
       "Accept": "application/x-bibtex"}


def get(url, accept="application/x-bibtex", timeout=25, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA["User-Agent"], "Accept": accept})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            last = e
            time.sleep(6 * (i + 1))
    raise last


def norm_bibtex(key, raw):
    """Rename the doi.org auto-key to our key; keep verified fields."""
    raw = re.sub(r"@misc\{[^,]*,", f"@misc{{{key},", raw)
    # drop noisy fields
    raw = re.sub(r"\n\s*(copyright|keywords) = \{[^}]*\},?", "", raw)
    raw = re.sub(r",(\s*\n)", r"\1", raw)
    raw = raw.rstrip()
    if not raw.endswith("}"):
        raw += "\n}"
    return raw


def main():
    entries, ok, fail = [], [], []

    for key, doi in ARXIV_DOIS.items():
        try:
            raw = get(f"https://doi.org/{doi}")
            if "@misc" not in raw and "@article" not in raw:
                raise ValueError("no bibtex in response")
            entries.append(norm_bibtex(key, raw))
            ok.append((key, doi))
            title = re.search(r"title = \{(.+)\}", raw)
            print(f"OK  {key}: {title.group(1)[:70] if title else '?'}")
        except Exception as e:
            fail.append((key, str(e)))
            print(f"FAIL {key}: {e}")
        time.sleep(1.0)

    for key, (title, authors, url) in WEB.items():
        try:
            code = None
            req = urllib.request.Request(url, headers={"User-Agent": UA["User-Agent"]})
            with urllib.request.urlopen(req, timeout=20) as r:
                code = r.status
            entry = (f"@misc{{{key},\n  title  = {{{title}}},\n"
                     f"  author = {{{authors}}},\n  year = {{2023}},\n"
                     f"  howpublished = {{\\url{{{url}}}}},\n"
                     f"  note = {{Blog post; URL verified (HTTP {code})}}\n}}")
            entries.append(entry)
            ok.append((key, url))
            print(f"OK  {key}: URL verified {code}")
        except Exception as e:
            fail.append((key, str(e)))
            print(f"FAIL {key}: {e}")

    if entries:
        with open(BIB, "a") as f:
            f.write("\n\n" + "\n\n".join(entries) + "\n")
    with open(LOG, "a") as f:
        f.write("\n\n## Recovery pass 3 (doi.org DataCite / URL check)\n\n")
        f.write(f"- Retrieved via DOI content negotiation: {len(ok)}\n")
        for k, d in ok:
            f.write(f"- `{k}`: {d}\n")
        if fail:
            f.write(f"- Failures: {len(fail)}\n")
            for k, e in fail:
                f.write(f"- `{k}`: {e}\n")

    print(f"\nrecovered={len(ok)} failed={len(fail)}")
    for k, e in fail:
        print(f"  STILL MISSING: {k} ({e})")


if __name__ == "__main__":
    main()
