# SAGE-v2 GPU extension (8K/16K) — summary

- GPU: Tesla T4 x2 (15.64 GB)
- torch 2.11.0+cu128 | transformers 5.16.1
- driver: ext8k

## PPL — qwen15b-ext8k

| policy | rho | gamma | tau | PPL | violations |
|---|---|---|---|---|---|
| full | 1.0 | None | None | 7.949 | 0 |
| h2o | 0.05 | None | None | 10.831 | 0 |
| h2o | 0.1 | None | None | 9.947 | 0 |
| h2o | 0.2 | None | None | 9.287 | 0 |
| pyramidkv | 0.05 | None | None | 11.423 | 0 |
| pyramidkv | 0.1 | None | None | 10.584 | 0 |
| pyramidkv | 0.2 | None | None | 9.775 | 0 |
| sage | 0.05 | None | None | 10.061 | 0 |
| sage | 0.1 | None | None | 9.249 | 0 |
| sage | 0.2 | None | None | 8.716 | 4 |
| sage-uniform | 0.2 | None | None | 8.661 | 0 |

## Needle — qwen15b-ext8k

| method | L | multi | mean hit-rate | mean retention |
|---|---|---|---|---|
| full | 8192 | False | 1.000 | 1.000 |
| full | 8192 | True | 1.000 | 1.000 |
| h2o | 8192 | False | 0.400 | 0.023 |
| h2o | 8192 | True | 0.000 | 0.022 |
| pyramidkv | 8192 | False | 0.200 | 0.036 |
| pyramidkv | 8192 | True | 0.000 | 0.036 |
| sage | 8192 | False | 0.200 | 0.242 |
| sage | 8192 | True | 0.333 | 0.320 |
| streamingllm | 8192 | False | 0.200 | 0.200 |

## PPL — qwen15b-ext16k

| policy | rho | gamma | tau | PPL | violations |
|---|---|---|---|---|---|
| full | 1.0 | None | None | 7.863 | 0 |
| h2o | 0.2 | None | None | 9.415 | 0 |
| pyramidkv | 0.2 | None | None | 9.899 | 0 |
| sage | 0.2 | None | None | 8.417 | 57 |
| sage-uniform | 0.2 | None | None | 8.373 | 0 |

## Needle — qwen15b-ext16k

| method | L | multi | mean hit-rate | mean retention |
|---|---|---|---|---|
| full | 16384 | False | 1.000 | 1.000 |
| h2o | 16384 | False | 0.667 | 0.040 |
| pyramidkv | 16384 | False | 0.000 | 0.042 |
| sage | 16384 | False | 0.333 | 0.369 |
| streamingllm | 16384 | False | 0.333 | 0.333 |
