"""Originality verification for the SAGE manuscript.

Checks across academic databases:
1. Exact paper title search (arXiv / OpenAlex / Crossref / Semantic Scholar)
2. Distinctive manuscript sentences via OpenAlex full-text search
3. Method-name ("SAGE" + KV cache) collision in title search
4. Author-name collision risk (Yifan Zhang / Jingwen Liu / Bo Chen)
"""
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = {"User-Agent": "originality-check/1.0 (mailto:check@example.org)"}


def get(url, retries=2):
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:  # noqa: BLE001
            if i == retries:
                return json.dumps({"_error": str(e)})
            time.sleep(4)
    return "{}"


TITLE = ("Sparsity-Adaptive Gated Eviction for Memory-Efficient "
         "Long-Context Inference of Large Language Models")

report = {}

# ---------- 1. exact title search ----------
print("=" * 70)
print("[1] EXACT TITLE SEARCH")
print("=" * 70)

# arXiv
q = urllib.parse.quote('all:"Sparsity-Adaptive Gated Eviction"')
xml_txt = get(f"http://export.arxiv.org/api/query?search_query={q}&max_results=5")
ns = {"a": "http://www.w3.org/2005/Atom"}
try:
    root = ET.fromstring(xml_txt)
    entries = root.findall("a:entry", ns)
    arxiv_titles = [e.findtext("a:title", "", ns).strip() for e in entries]
    print(f"  arXiv phrase match          : {len(arxiv_titles)} hits -> {arxiv_titles}")
    report["arxiv_exact"] = arxiv_titles
except Exception as e:  # noqa: BLE001
    print(f"  arXiv parse error: {e}")
    report["arxiv_exact"] = f"error: {e}"
time.sleep(3)

# OpenAlex title search
flt = urllib.parse.quote('title.search:"Sparsity-Adaptive Gated Eviction"')
oa_txt = get(f"https://api.openalex.org/works?filter={flt}&per_page=5")
try:
    oa = json.loads(oa_txt)
    hits = [w["display_name"] for w in oa.get("results", [])]
    print(f"  OpenAlex title search       : {len(hits)} hits -> {hits}")
    report["openalex_exact"] = hits
except Exception as e:  # noqa: BLE001
    print(f"  OpenAlex parse error: {e} / raw: {oa_txt[:200]}")
    report["openalex_exact"] = f"error: {e}"

# Crossref bibliographic
cr_txt = get("https://api.crossref.org/works?query.bibliographic="
             + urllib.parse.quote(TITLE) + "&rows=4&select=title,score")
try:
    cr = json.loads(cr_txt)
    hits = [it["title"][0] for it in cr.get("message", {}).get("items", [])]
    scores = [round(it.get("score", 0), 1) for it in cr.get("message", {}).get("items", [])]
    print(f"  Crossref bibliographic      : {len(hits)} hits")
    for t, s in zip(hits, scores):
        print(f"    [{s}] {t[:90]}")
    report["crossref_exact"] = hits
except Exception as e:  # noqa: BLE001
    print(f"  Crossref parse error: {e}")
    report["crossref_exact"] = f"error: {e}"

# Semantic Scholar
ss_txt = get("https://api.semanticscholar.org/graph/v1/paper/search?query="
             + urllib.parse.quote('"Sparsity-Adaptive Gated Eviction"')
             + "&fields=title,year&limit=5")
try:
    ss = json.loads(ss_txt)
    hits = [(p.get("title"), p.get("year")) for p in ss.get("data", [])]
    print(f"  Semantic Scholar            : {ss.get('total')} total, top -> {hits}")
    report["s2_exact"] = hits
except Exception as e:  # noqa: BLE001
    print(f"  S2 limited/failed: {ss_txt[:120]}")
    report["s2_exact"] = f"error: {ss_txt[:120]}"

# ---------- 2. distinctive sentence full-text search ----------
print()
print("=" * 70)
print("[2] DISTINCTIVE SENTENCES (OpenAlex fulltext.search)")
print("=" * 70)
sentences = [
    "dual-reservoir structure that protects a recent window",
    "attention-confidence score that tracks the current relevance",
    "layer-adaptive budget allocator that distributes cache capacity",
]
report["sentences"] = {}
for s in sentences:
    flt = urllib.parse.quote(f'fulltext.search:"{s}"')
    t = get(f"https://api.openalex.org/works?filter={flt}&per_page=5&select=id,display_name")
    try:
        d = json.loads(t)
        hits = [w["display_name"] for w in d.get("results", [])]
        print(f"  [{len(hits)} hits] {s[:60]}")
        for h in hits:
            print(f"      -> {h[:85]}")
        report["sentences"][s] = hits
    except Exception as e:  # noqa: BLE001
        print(f"  [error] {s[:50]}: {e}")
        report["sentences"][s] = f"error: {e}"
    time.sleep(1)

# ---------- 3. SAGE method-name collision ----------
print()
print("=" * 70)
print("[3] METHOD NAME 'SAGE' + KV CACHE COLLISION (title search)")
print("=" * 70)
for qtxt, label in [
    ('title.search:"SAGE" KV cache', "OpenAlex: SAGE + KV cache"),
    ('title.search:"SAGE" cache eviction', "OpenAlex: SAGE + cache eviction"),
    ('title.search:"SAGE" LLM inference', "OpenAlex: SAGE + LLM inference"),
]:
    flt = urllib.parse.quote(qtxt)
    t = get(f"https://api.openalex.org/works?filter={flt}&per_page=8&select=display_name,publication_year")
    try:
        d = json.loads(t)
        hits = [(w["display_name"], w.get("publication_year")) for w in d.get("results", [])]
        print(f"  {label}: {len(hits)} hits")
        for h, y in hits:
            print(f"      -> ({y}) {h[:85]}")
        report.setdefault("sage_name", {})[label] = hits
    except Exception as e:  # noqa: BLE001
        print(f"  {label}: error {e}")
    time.sleep(1)

q = urllib.parse.quote('ti:"SAGE" AND abs:"KV cache"')
xml_txt = get(f"http://export.arxiv.org/api/query?search_query={q}&max_results=8")
try:
    root = ET.fromstring(xml_txt)
    entries = root.findall("a:entry", ns)
    hits = [e.findtext("a:title", "", ns).strip() for e in entries]
    print(f"  arXiv: ti:SAGE + abs:'KV cache': {len(hits)} hits")
    for h in hits:
        print(f"      -> {h[:90]}")
    report.setdefault("sage_name", {})["arxiv"] = hits
except Exception as e:  # noqa: BLE001
    print(f"  arXiv parse error: {e}")

# ---------- 4. author collision risk ----------
print()
print("=" * 70)
print("[4] AUTHOR-NAME COLLISION RISK (informational)")
print("=" * 70)
report["authors"] = {}
for name in ["Yifan Zhang", "Jingwen Liu", "Bo Chen"]:
    t = get("https://api.openalex.org/authors?search=" + urllib.parse.quote(name)
            + "&per_page=5&select=display_name,last_known_institutions")
    try:
        d = json.loads(t)
        rows = []
        for a in d.get("results", []):
            insts = a.get("last_known_institutions") or []
            inst = insts[0]["display_name"] if insts else "?"
            rows.append(f"{a['display_name']} @ {inst}")
        print(f"  '{name}': {d.get('meta', {}).get('count')} authors exist in OpenAlex; top:")
        for r in rows[:4]:
            print(f"      -> {r}")
        report["authors"][name] = rows
    except Exception as e:  # noqa: BLE001
        print(f"  '{name}': error {e}")
    time.sleep(1)

with open("/home/z/my-project/tool-results/orig_check_report.json", "w") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
print()
print("report saved -> tool-results/orig_check_report.json")
