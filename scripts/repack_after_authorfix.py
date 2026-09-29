"""Rebuild the SAGE paper package after the author-block fix.

1. Rebuild SAGE_paper_package.zip (paper/ + research-repo/ + scripts/)
2. Refresh download/ deliverables (PDF + ZIP)
3. Sync github-upload/ (paper sources, review fulltext, top-level files)
4. Compare old vs new zip file sets for structural parity
"""
import os
import shutil
import zipfile

BASE = "/home/z/my-project"
PAPER = f"{BASE}/paper-project/paper"
REPO = f"{BASE}/paper-project/research-repo"
SCRIPTS = f"{BASE}/scripts"
DL = f"{BASE}/download"
GH = f"{BASE}/github-upload"

old_zip = f"{DL}/SAGE_paper_package.zip"
old_names = set(zipfile.ZipFile(old_zip).namelist()) if os.path.exists(old_zip) else set()

# ---------- 1. rebuild zip ----------
tmp_zip = f"{DL}/SAGE_paper_package.zip.new"
z = zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED)
count = 0
for root, _dirs, files in os.walk(PAPER):
    for f in sorted(files):
        if f == "main.pdf":
            continue  # parity with original package layout
        full = os.path.join(root, f)
        z.write(full, "paper/" + os.path.relpath(full, PAPER))
        count += 1
for root, _dirs, files in os.walk(REPO):
    for f in sorted(files):
        full = os.path.join(root, f)
        z.write(full, "research-repo/" + os.path.relpath(full, REPO))
        count += 1
script_files = sorted(
    f for f in os.listdir(SCRIPTS)
    if f.endswith(".py") and f not in ("vlm_check",)
)
for f in script_files:
    z.write(os.path.join(SCRIPTS, f), "scripts/" + f)
    count += 1
z.close()
os.replace(tmp_zip, old_zip)
print(f"zip rebuilt: {count} files -> {old_zip}")

new_names = set(zipfile.ZipFile(old_zip).namelist())
added = sorted(n for n in new_names - old_names if not n.endswith("/"))
removed = sorted(n for n in old_names - new_names if not n.endswith("/"))
print("added vs old zip  :", added)
print("removed vs old zip:", removed)

# ---------- 2. refresh download deliverables ----------
shutil.copy2(f"{PAPER}/main.pdf", f"{DL}/SAGE_AppliedIntelligence_Manuscript.pdf")
print("download PDF refreshed")

# ---------- 3. sync github-upload ----------
os.makedirs(f"{GH}/paper", exist_ok=True)
for root, _dirs, files in os.walk(PAPER):
    for f in sorted(files):
        if f == "main.pdf":
            continue
        src = os.path.join(root, f)
        rel = os.path.relpath(src, PAPER)
        dst = os.path.join(GH, "paper", rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
# research-repo + scripts unchanged, but sync scripts (orig_check.py added)
for root, _dirs, files in os.walk(REPO):
    for f in sorted(files):
        src = os.path.join(root, f)
        rel = os.path.relpath(src, REPO)
        dst = os.path.join(GH, "research-repo", rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
for f in script_files:
    shutil.copy2(os.path.join(SCRIPTS, f), os.path.join(GH, "scripts", f))
shutil.copy2(f"{PAPER}/main.pdf", f"{GH}/SAGE_AppliedIntelligence_Manuscript.pdf")
shutil.copy2(old_zip, f"{GH}/SAGE_paper_package.zip")
print("github-upload synced")

# residual name scan across the whole upload tree
import re
pat = re.compile(r"Yifan|Jingwen|yifanzhang|jingwenliu|bochen|zju\.edu\.cn|fudan\.edu\.cn")
hits = []
for root, _dirs, files in os.walk(GH):
    if ".git" in root:
        continue
    for f in files:
        p = os.path.join(root, f)
        try:
            if f.endswith((".tex", ".txt", ".md", ".bib", ".yaml", ".csv", ".html")):
                txt = open(p, encoding="utf-8", errors="ignore").read()
                if pat.search(txt):
                    hits.append(p)
        except Exception:
            pass
print("residual real-name matches in github-upload:", hits if hits else "NONE")
