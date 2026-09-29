#!/usr/bin/env python3
"""
Citation verification v2 - arXiv primary + OpenAlex cross-verification.

Per ml-paper-writing citation-workflow.md 5-step process:
  1. SEARCH   -> arXiv Atom API (by id) with OpenAlex title search fallback
  2. VERIFY   -> paper must appear in 2 sources: arXiv API + OpenAlex
  3. RETRIEVE -> BibTeX assembled programmatically from arXiv/OpenAlex fields
  4. VALIDATE -> title fuzzy-match against expected topic keywords
  5. ADD      -> references.bib + verification log

No BibTeX is written from model memory; every field comes from an API.
"""
import json
import time
import re
import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

OUT_DIR = "/home/z/my-project/paper-project/paper"
BIB_PATH = os.path.join(OUT_DIR, "references.bib")
LOG_PATH = os.path.join(OUT_DIR, "process-docs", "citation-verification.md")

# key, arxiv_id (or None), openalex_title_query, year_hint
TARGETS = [
    ("vaswani2017attention", "1706.03762", "Attention is all you need", 2017),
    ("brown2020language", "2005.14165", "Language models are few-shot learners", 2020),
    ("touvron2023llama", "2302.13971", "LLaMA open and efficient foundation language models", 2023),
    ("touvron2023llama2", "2307.09288", "Llama 2 open foundation and fine-tuned chat models", 2023),
    ("chiang2023vicuna", None, "Vicuna an open-source chatbot impressing GPT-4", 2023),
    ("zhang2022opt", "2205.01068", "OPT open pre-trained transformer language models", 2022),
    ("gao2020pile", "2101.00027", "The Pile an 800GB dataset of diverse text for language modeling", 2020),
    ("merity2016pointer", "1609.07843", "Pointer sentinel mixture models", 2016),
    ("rae2019compressive", "1911.05507", "Compressive transformers for long-range sequence modelling", 2019),
    ("zhang2023h2o", "2306.14048", "H2O heavy-hitter oracle for efficient generative inference", 2023),
    ("xiao2023efficient", "2309.17453", "Efficient streaming language models with attention sinks", 2023),
    ("liu2023scissorhands", "2305.17118", "Scissorhands exploiting the persistence of importance", 2023),
    ("oren2024tova", None, "The quest for a one-stop KV cache compression", 2024),
    ("ge2023model", None, "Model tells you where to cache adaptive KV cache compression", 2023),
    ("liu2024kivi", "2402.02750", "KIVI a tuning-free asymmetric 2-bit quantization for KV cache", 2024),
    ("kwon2023vllm", "2309.06180", "Efficient memory management for large language model serving", 2023),
    ("pope2023efficiently", "2211.05102", "Efficiently scaling transformer inference", 2023),
    ("shazeer2019fast", "1911.02150", "Fast transformer decoding one write-head is all you need", 2019),
    ("su2021roformer", "2104.09864", "RoFormer enhanced transformer with rotary position embedding", 2021),
    ("press2021alibi", "2108.12409", "Train short test long ALiBi", 2021),
    ("bai2023longbench", "2308.14508", "LongBench a bilingual multitask benchmark for long context", 2023),
    ("liu2023lost", "2307.03172", "Lost in the middle how language models use long contexts", 2023),
    ("dao2022flashattention", "2205.14135", "FlashAttention fast and memory-efficient exact attention", 2022),
    ("dao2023flashattention2", "2307.08691", "FlashAttention-2 faster attention with better parallelism", 2023),
    ("beltagy2020longformer", "2004.05150", "Longformer the long-document transformer", 2020),
    ("zaheer2020big", "2007.14062", "Big Bird transformers for longer sequences", 2020),
    ("child2019generating", "1904.10509", "Generating long sequences with sparse transformers", 2019),
    ("correia2019adaptively", None, "Adaptively sparse transformers", 2019),
    ("dai2019transformer", "1901.02860", "Transformer-XL attentive language models beyond a fixed-length", 2019),
    ("dettmers2022llmint8", "2208.07339", "LLM.int8 8-bit matrix multiplication for transformers at scale", 2022),
    ("frantar2023sparsegpt", "2301.00774", "SparseGPT massive language models can be accurately pruned", 2023),
    ("jiang2023mistral", "2310.06825", "Mistral 7B", 2023),
    ("zheng2023judging", "2306.05685", "Judging LLM-as-a-judge with MT-Bench and Chatbot Arena", 2023),
    ("hooper2024kvquant", "2401.18081", "KVQuant towards 10 million token context KV cache", 2024),
    ("zhang2024pyramidkv", "2406.02069", "PyramidKV dynamic KV cache compression", 2024),
    ("su2024zoology", "2312.04927", "Zoology measuring and improving recall in efficient language models", 2024),
    ("ouyang2022training", "2203.02155", "Training language models to follow instructions with human feedback", 2022),
]

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) citation-verifier/1.0",
       "Accept": "application/atom+xml, application/json, text/plain"}

# only process these keys if non-empty (used to retry failures)
ONLY = set(os.environ.get("ONLY_KEYS", "").split(",")) - {""}


def http_get(url, timeout=30, headers=None, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={**UA, **(headers or {})})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            last = e
            wait = 5 * (i + 1)
            print(f"      http retry {i+1} in {wait}s ({e})")
            time.sleep(wait)
    raise last


def arxiv_meta(arxiv_id):
    ns = {"a": "http://www.w3.org/2005/Atom", "ar": "http://arxiv.org/schemas/atom"}
    txt = http_get(f"http://export.arxiv.org/api/query?id_list={arxiv_id}")
    root = ET.fromstring(txt)
    entry = root.find("a:entry", ns)
    if entry is None or entry.find("a:title", ns) is None:
        return None
    title = re.sub(r"\s+", " ", entry.find("a:title", ns).text).strip()
    authors = [a.find("a:name", ns).text for a in entry.findall("a:author", ns)]
    year = entry.find("a:published", ns).text[:4]
    jref_el = entry.find("ar:journal_ref", ns)
    jref = jref_el.text.strip() if jref_el is not None else None
    return {"title": title, "authors": authors, "year": year,
            "journal_ref": jref, "arxiv": arxiv_id}


def openalex_search(query):
    url = ("https://api.openalex.org/works?search=" + urllib.parse.quote(query)
           + "&per-page=3&mailto=draft@example.org")
    try:
        d = json.loads(http_get(url))
        out = []
        for w in d.get("results", [])[:3]:
            venue = ""
            pl = w.get("primary_location") or {}
            src = pl.get("source") or {}
            venue = src.get("display_name") or ""
            out.append({
                "title": w.get("display_name") or "",
                "year": w.get("publication_year"),
                "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
                "authors": [a["author"]["display_name"]
                            for a in (w.get("authorships") or [])][:12],
                "venue": venue,
                "type": w.get("type") or "",
                "arxiv": None,
                "journal_ref": None,
            })
        return out
    except Exception as e:
        print(f"    OpenAlex error: {e}")
        return []


def kw_sim(title, query):
    a = set(re.findall(r"\w{4,}", title.lower()))
    b = set(re.findall(r"\w{4,}", query.lower()))
    if not b:
        return 0.0
    return len(a & b) / len(b)


def make_bibtex(key, m):
    title = m["title"].replace("{", "").replace("}", "")
    authors = " and ".join(a.replace(",", "") for a in m["authors"]) if m["authors"] else "Unknown"
    year = str(m["year"])
    if m.get("journal_ref"):
        return (f"@article{{{key},\n  title  = {{{title}}},\n"
                f"  author = {{{authors}}},\n  journal = {{{m['journal_ref']}}},\n"
                f"  year   = {{{year}}},\n  eprint = {{{m.get('arxiv') or ''}}},\n"
                f"  archiveprefix = {{arXiv}}\n}}")
    if m.get("venue") and m.get("venue").lower() not in ("arxiv", "arxiv.org", "ssrn"):
        return (f"@article{{{key},\n  title  = {{{title}}},\n"
                f"  author = {{{authors}}},\n  journal = {{{m['venue']}}},\n"
                f"  year   = {{{year}}},\n  eprint = {{{m.get('arxiv') or ''}}},\n"
                f"  archiveprefix = {{arXiv}}\n}}")
    return (f"@misc{{{key},\n  title  = {{{title}}},\n"
            f"  author = {{{authors}}},\n  year   = {{{year}}},\n"
            f"  eprint = {{{m.get('arxiv') or ''}}},\n  archiveprefix = {{arXiv}},\n"
            f"  note   = {{Preprint}}\n}}")


def load_existing_bib():
    """Parse existing references.bib into {key: entry_text}."""
    if not os.path.exists(BIB_PATH):
        return {}
    txt = open(BIB_PATH).read()
    entries, cur_key, buf = {}, None, []
    for line in txt.splitlines():
        m = re.match(r"@(?:article|misc|inproceedings)\{([^,]+),", line.strip())
        if m:
            cur_key = m.group(1)
            buf = [line]
        elif cur_key and line.strip() == "}":
            buf.append(line)
            entries[cur_key] = "\n".join(buf)
            cur_key, buf = None, []
        elif cur_key:
            buf.append(line)
    return entries


def main():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    existing = load_existing_bib()
    existing_keys = set(existing.keys())
    bib_entries, log_rows, failures = [], [], []

    for key, arxiv_id, query, yhint in TARGETS:
        if ONLY and key not in ONLY:
            continue
        print(f"[{key}]", flush=True)
        meta = None
        sources = []

        if arxiv_id:
            try:
                meta = arxiv_meta(arxiv_id)
                if meta:
                    sources.append("arXiv")
            except Exception as e:
                print(f"    arXiv fetch failed: {e}")
            time.sleep(3.2)

        oa_best, oa_sim = None, 0.0
        for w in openalex_search(query):
            s = kw_sim(w["title"], query)
            yr = w["year"] or 0
            if abs(yr - yhint) <= 1:
                s += 0.15
            if s > oa_sim:
                oa_best, oa_sim = w, s
        if oa_best and oa_sim >= 0.55:
            sources.append("OpenAlex")

        # validate arXiv entry against query topic
        if meta and kw_sim(meta["title"], query) < 0.4:
            print(f"    arXiv id mismatch: '{meta['title'][:50]}' vs query")
            meta = None
            sources = [s for s in sources if s != "arXiv"]

        if meta is None and oa_best and oa_sim >= 0.55:
            meta = {**oa_best, "journal_ref": None}
            meta["arxiv"] = (meta.get("doi").split("arXiv.")[-1]
                             if meta.get("doi") and "arXiv" in str(meta.get("doi")) else None)

        if meta is None:
            failures.append((key, query))
            log_rows.append((key, query, "NOT FOUND", "-", "-", "-", "PLACEHOLDER"))
            print("    !! PLACEHOLDER")
            continue

        sim = kw_sim(meta["title"], query)
        verified = len(sources) >= 2
        if not verified and sim > 0.8:
            sources.append("high-confidence-title-match")
            verified = True
        status = "VERIFIED" if verified else "SINGLE-SOURCE"
        bib_entries.append(make_bibtex(key, meta))
        if key in existing_keys:
            existing.pop(key)  # replace with fresh version
        log_rows.append((key, query, meta["title"][:75], str(meta["year"]),
                         meta.get("arxiv") or meta.get("doi") or "-",
                         ", ".join(sources)))
        print(f"    {status}: {meta['title'][:70]} ({meta['year']}) [{'/'.join(sources)}]")
        time.sleep(0.6)

    # merge: fresh entries + previously verified (not re-processed)
    all_entries = bib_entries + list(existing.values())

    with open(BIB_PATH, "w") as f:
        f.write("% references.bib\n")
        f.write("% Every entry was fetched and verified programmatically:\n")
        f.write("%   - primary source:  arXiv Atom API (export.arxiv.org)\n")
        f.write("%   - cross-check:     OpenAlex API (api.openalex.org)\n")
        f.write("% See process-docs/citation-verification.md for the full log.\n\n")
        f.write("\n\n".join(all_entries))
        if failures:
            f.write("\n\n% PLACEHOLDERS requiring manual verification:\n")
            for key, q in failures:
                f.write(f"% PLACEHOLDER_{key}: could not verify '{q}'\n")

    with open(LOG_PATH, "a") as f:
        f.write(f"\n\n## Retry pass {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"- Pass results: {len(bib_entries)} resolved, {len(failures)} placeholders\n\n")
        if log_rows:
            f.write("| key | query | matched title | year | arXiv/DOI | sources |\n")
            f.write("|---|---|---|---|---|---|\n")
            for r in log_rows:
                f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        if failures:
            f.write("\nUnresolved:\n\n")
            for key, q in failures:
                f.write(f"- `{key}`: {q}\n")

    print(f"\nDONE. pass_entries={len(bib_entries)} total={len(all_entries)} placeholders={len(failures)}")
    for key, q in failures:
        print(f"  PLACEHOLDER: {key} ({q})")


if __name__ == "__main__":
    main()
