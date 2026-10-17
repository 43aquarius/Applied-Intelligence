#!/bin/bash
# SAGE v2 setup - phase 2 (torch from local wheel, deps from aliyun pypi mirror)
set -x
cd /home/z/my-project
export HF_ENDPOINT=https://hf-mirror.com
PYPI="-i https://mirrors.aliyun.com/pypi/simple/"

python3 -m pip install --no-cache-dir /home/z/my-project/sage2/wheels/torch-2.14.1+cpu-cp312-cp312-manylinux_2_28_x86_64.whl
python3 -m pip install --no-cache-dir $PYPI transformers datasets safetensors matplotlib pandas scipy sentencepiece tiktoken accelerate

# verify imports
python3 -c "import torch, transformers, numpy; print('IMPORT_OK torch', torch.__version__, 'transformers', transformers.__version__)"

# models + data via hf-mirror
python3 - <<'EOF'
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
from huggingface_hub import snapshot_download, hf_hub_download
for repo in ["openai-community/gpt2", "Qwen/Qwen2.5-0.5B-Instruct"]:
    for attempt in range(5):
        try:
            p = snapshot_download(repo, allow_patterns=["*.json", "*.safetensors", "tokenizer*", "merges*", "vocab*", "*.model", "*.txt"])
            print("MODEL_OK", repo, p, flush=True)
            break
        except Exception as e:
            print("RETRY", repo, attempt, repr(e), flush=True)
for attempt in range(5):
    try:
        p = hf_hub_download("Salesforce/wikitext", "wikitext-2-raw-v1/test-00000-of-00001.parquet", repo_type="dataset")
        print("WIKITEXT_OK", p, flush=True)
        break
    except Exception as e:
        print("RETRY wikitext", attempt, repr(e), flush=True)
EOF
echo "SETUP_DONE"
