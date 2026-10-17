#!/bin/bash
cd /home/z/my-project/models/qwen05b
for f in config.json generation_config.json tokenizer_config.json vocab.json merges.txt; do
  curl -sL --connect-timeout 15 --speed-time 20 --speed-limit 10000 -m 120 "https://hf-mirror.com/Qwen/Qwen2.5-0.5B-Instruct/resolve/main/$f" -o "$f" && echo "OK $f"
done
for f in tokenizer.json model.safetensors; do
  for i in 1 2 3 4 5; do
    curl -sL --connect-timeout 15 --speed-time 25 --speed-limit 50000 -m 900 "https://hf-mirror.com/Qwen/Qwen2.5-0.5B-Instruct/resolve/main/$f" -o "$f" && s=$(wc -c < "$f") && [ "$s" -gt 1000000 ] && echo "OK $f $s" && break || sleep 5
  done
done
curl -sL --connect-timeout 15 --speed-time 20 --speed-limit 10000 -m 300 "https://hf-mirror.com/datasets/Salesforce/wikitext/resolve/main/wikitext-2-raw-v1/test-00000-of-00001.parquet" -o /home/z/my-project/models/wikitext2-test.parquet && echo "OK wikitext $(wc -c < /home/z/my-project/models/wikitext2-test.parquet)"
echo QWEN_DL_DONE
