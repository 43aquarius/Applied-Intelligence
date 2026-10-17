#!/usr/bin/env python3
"""Merge cover + body into the final paper PDF (A4-normalised)."""
from pypdf import PdfReader, PdfWriter

A4_W, A4_H = 595.28, 841.89


def normalize(page):
    w, h = float(page.mediabox.width), float(page.mediabox.height)
    if abs(w - A4_W) > 2 or abs(h - A4_H) > 2:
        page.scale_to(A4_W, A4_H)
    return page


writer = PdfWriter()
writer.add_page(normalize(PdfReader("cover.pdf").pages[0]))
for p in PdfReader("main.pdf").pages:
    writer.add_page(normalize(p))
with open("final.pdf", "wb") as f:
    writer.write(f)
print("MERGED -> final.pdf,", len(writer.pages), "pages")
