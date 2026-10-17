#!/usr/bin/env python3
"""Robust wheel fetcher: resolve package URLs from the Aliyun PyPI mirror
and download via curl with stall protection (this network stalls pip's
downloader on large files)."""
import re
import subprocess
import sys
import urllib.request

MIRROR = "https://mirrors.aliyun.com/pypi/simple"
WHEELS = "/home/z/my-project/sage2/wheels"

PACKAGES = sys.argv[1:] or [
    "transformers", "datasets", "safetensors", "matplotlib", "pandas",
    "scipy", "sentencepiece", "tiktoken", "accelerate", "huggingface-hub",
    "tokenizers", "regex", "requests", "pyyaml", "packaging", "filelock",
    "tqdm", "networkx", "jinja2", "fsspec", "typing-extensions",
]


def best_wheel_url(pkg: str):
    url = f"{MIRROR}/{pkg}/"
    req = urllib.request.Request(url, headers={"User-Agent": "pip/25"})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode()
    links = re.findall(r'href="([^"]+)"', html)
    from urllib.parse import urljoin
    cands = []
    for link in links:
        link = link.split("#")[0]          # strip sha256 fragment
        name = link.rsplit("/", 1)[-1]
        if not name.endswith(".whl"):
            continue
        score = 0
        if "cp312" in name and ("manylinux" in name or "linux_x86_64" in name):
            score = 3
        elif "py3-none-any" in name or "py2.py3-none-any" in name:
            score = 2
        elif "cp312" in name:
            score = 1
        if score:
            cands.append((score, name, urljoin(url, link)))
    if not cands:
        return None, None
    cands.sort(key=lambda x: (x[0], x[1]))
    score, name, link = cands[-1]
    return name, link


def curl(url: str, out: str) -> bool:
    cmd = [
        "curl", "-sL", "--connect-timeout", "15", "--speed-time", "20",
        "--speed-limit", "20000", "-m", "420", "--retry", "3", url, "-o", out,
    ]
    return subprocess.run(cmd).returncode == 0


for pkg in PACKAGES:
    name, url = best_wheel_url(pkg)
    if not url:
        print(f"SKIP {pkg}: no wheel found", flush=True)
        continue
    out = f"{WHEELS}/{name}"
    import os
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        print(f"HAVE {name}", flush=True)
        continue
    ok = curl(url, out)
    size = os.path.getsize(out) if os.path.exists(out) else 0
    print(("OK " if ok and size > 1000 else "FAIL ") + f"{name} {size}",
          flush=True)
print("FETCH_WHEELS_DONE", flush=True)
