"""Minimal debug: find where the mask mismatch originates."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import DynamicCache

model = AutoModelForCausalLM.from_pretrained(
    "/home/z/my-project/models/gpt2", dtype=torch.float32,
    attn_implementation="eager").eval()
tok = AutoTokenizer.from_pretrained("/home/z/my-project/models/gpt2")
ids = tok("The quick brown fox jumps over the lazy dog. " * 4,
          return_tensors="pt").input_ids
print("n tokens:", ids.shape)

# --- chunk 1 (no cache)
q1 = ids[:, :8]
out1 = model(input_ids=q1, attention_mask=torch.ones(1, 8, dtype=torch.long),
             position_ids=torch.arange(8).unsqueeze(0),
             output_attentions=True, use_cache=True,
             cache_position=torch.arange(8))
print("chunk1 ok, cache len:", len(out1.past_key_values))
print("att shape:", out1.attentions[0].shape)
k1 = out1.attentions[0].shape[-1]
print("k axis:", k1)

# --- inspect cache object type and layers
pkv = out1.past_key_values
print("cache type:", type(pkv).__name__)
if hasattr(pkv, "layers"):
    lay = pkv.layers[0]
    print("layer type:", type(lay).__name__)
    print("layer attrs:", [a for a in dir(lay) if not a.startswith("_")][:20])
    for attr in ("keys", "values", "key", "value"):
        t = getattr(lay, attr, None)
        if t is not None:
            print(f"  {attr}: {tuple(t.shape)}")

# --- chunk 2 with a rebuilt cache
dc = DynamicCache()
k, v = pkv.layers[0].keys, pkv.layers[0].values  # try attr names later
# extract all layers
pairs = []
for lay in pkv.layers:
    pairs.append((lay.keys, lay.values))
for l, (kk, vv) in enumerate(pairs):
    dc.update(kk, vv, l)
q2 = ids[:, 8:16]
out2 = model(input_ids=q2, past_key_values=dc,
             attention_mask=torch.ones(1, 8 + 8, dtype=torch.long),
             position_ids=torch.arange(8, 16).unsqueeze(0),
             output_attentions=True, use_cache=True,
             cache_position=torch.arange(8, 16))
print("chunk2 ok, att shape:", out2.attentions[0].shape)
print("DEBUG_OK")
