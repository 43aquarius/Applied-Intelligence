#!/bin/bash
# SAGE v2 redo - environment setup (CPU-only)
set -x
cd /home/z/my-project
export HF_ENDPOINT=https://hf-mirror.com

# 1) CPU-only PyTorch + core deps
python3 -m pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
python3 -m pip install --no-cache-dir transformers datasets accelerate safetensors matplotlib pandas scipy sentencepiece tiktoken

# 2) Models via hf-mirror
python3 - <<'EOF'
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
from huggingface_hub import snapshot_download
for repo in ["openai-community/gpt2", "Qwen/Qwen2.5-0.5B-Instruct"]:
    for attempt in range(3):
        try:
            p = snapshot_download(repo, allow_patterns=["*.json", "*.safetensors", "tokenizer*", "merges*", "vocab*", "*.model"])
            print("MODEL_OK", repo, p, flush=True)
            break
        except Exception as e:
            print("RETRY", repo, attempt, repr(e), flush=True)
EOF

# 3) WikiText-2 test set (parquet via hf-mirror)
python3 - <<'EOF'
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
from huggingface_hub import hf_hub_download
for attempt in range(3):
    try:
        p = hf_hub_download("Salesforce/wikitext", "wikitext-2-raw-v1/test-00000-of-00001.parquet", repo_type="dataset")
        print("WIKITEXT_OK", p, flush=True)
        break
    except Exception as e:
        print("RETRY wikitext", attempt, repr(e), flush=True)
EOF

echo "SETUP_DONE"
