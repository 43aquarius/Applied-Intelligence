#!/usr/bin/env python3
"""Download models + data via hf-mirror (run in background)."""
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from huggingface_hub import snapshot_download, hf_hub_download

for repo in ["openai-community/gpt2", "Qwen/Qwen2.5-0.5B-Instruct"]:
    for attempt in range(6):
        try:
            p = snapshot_download(
                repo,
                allow_patterns=["*.json", "*.safetensors", "tokenizer*",
                                "merges*", "vocab*", "*.model", "*.txt"],
                max_workers=2,
            )
            print("MODEL_OK", repo, p, flush=True)
            break
        except Exception as e:
            print("RETRY", repo, attempt, repr(e), flush=True)

for attempt in range(6):
    try:
        p = hf_hub_download(
            "Salesforce/wikitext",
            "wikitext-2-raw-v1/test-00000-of-00001.parquet",
            repo_type="dataset",
        )
        print("WIKITEXT_OK", p, flush=True)
        break
    except Exception as e:
        print("RETRY wikitext", attempt, repr(e), flush=True)
print("DOWNLOADS_DONE", flush=True)
