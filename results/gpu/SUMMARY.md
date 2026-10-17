# SAGE-v2 GPU replication — summary

- GPU: Tesla T4 x2 (15.64 GB)
- torch 2.11.0+cu128 | transformers 5.16.1
- Total: 34 PPL runs, 695,980 tokens, 0 budget violations

## PPL — Qwen2.5-1.5B-Instruct

| policy | rho | gamma | tau | PPL | violations |
|---|---|---|---|---|---|
| full | 1.0 | None | None | 8.801 | 0 |
| h2o | 0.05 | None | None | 12.705 | 0 |
| h2o | 0.1 | None | None | 11.460 | 0 |
| h2o | 0.2 | None | None | 10.505 | 0 |
| h2o | 0.3 | None | None | 10.042 | 0 |
| pyramidkv | 0.05 | None | None | 13.831 | 0 |
| pyramidkv | 0.1 | None | None | 12.594 | 0 |
| pyramidkv | 0.2 | None | None | 11.356 | 0 |
| pyramidkv | 0.3 | None | None | 10.767 | 0 |
| reverse-pyramid | 0.2 | None | None | 10.579 | 0 |
| sage | 0.05 | None | None | 12.976 | 0 |
| sage | 0.1 | None | None | 11.462 | 0 |
| sage | 0.2 | 0.98 | None | 10.498 | 0 |
| sage | 0.2 | 0.99 | None | 10.451 | 0 |
| sage | 0.2 | 0.999 | None | 10.549 | 0 |
| sage | 0.2 | 1.0 | None | 10.649 | 0 |
| sage | 0.2 | None | 0.5 | 10.340 | 0 |
| sage | 0.2 | None | 1.0 | 10.385 | 0 |
| sage | 0.2 | None | 2.0 | 10.495 | 0 |
| sage | 0.2 | None | None | 10.419 | 0 |
| sage | 0.3 | None | None | 9.943 | 0 |
| sage-nodecay | 0.2 | None | None | 10.649 | 0 |
| sage-norecent | 0.2 | None | None | 11.276 | 0 |
| sage-nosink | 0.2 | None | None | 46.368 | 0 |
| sage-uniform | 0.2 | None | None | 10.302 | 0 |
| streamingllm | 0.2 | None | None | 11.306 | 0 |

## Needle — Qwen2.5-1.5B-Instruct

| method | L | multi | mean hit-rate |
|---|---|---|---|
| full | 2048 | False | 1.000 |
| full | 4096 | False | 1.000 |
| h2o | 2048 | False | 0.000 |
| h2o | 4096 | False | 0.333 |
| pyramidkv | 2048 | False | 0.000 |
| pyramidkv | 4096 | False | 0.000 |
| sage | 2048 | False | 0.200 |
| sage | 4096 | False | 0.333 |
| streamingllm | 2048 | False | 0.200 |
| streamingllm | 4096 | False | 0.333 |
| full | 2048 | True | 1.000 |
| full | 4096 | True | 1.000 |
| h2o | 2048 | True | 0.000 |
| h2o | 4096 | True | 0.667 |
| pyramidkv | 2048 | True | 0.000 |
| pyramidkv | 4096 | True | 0.000 |
| sage | 2048 | True | 0.333 |
| sage | 4096 | True | 0.333 |
| sage-nodecay | 2048 | True | 0.000 |
| sage-nodecay | 4096 | True | 0.000 |

## PPL — Qwen2.5-3B-Instruct

| policy | rho | gamma | tau | PPL | violations |
|---|---|---|---|---|---|
| full | 1.0 | None | None | 7.775 | 0 |
| h2o | 0.2 | None | None | 9.360 | 0 |
| pyramidkv | 0.2 | None | None | 10.548 | 0 |
| reverse-pyramid | 0.2 | None | None | 9.360 | 0 |
| sage | 0.2 | None | None | 9.278 | 0 |
| sage-nodecay | 0.2 | None | None | 9.480 | 0 |
| sage-uniform | 0.2 | None | None | 9.188 | 0 |
| streamingllm | 0.2 | None | None | 10.105 | 0 |

## Needle — Qwen2.5-3B-Instruct

| method | L | multi | mean hit-rate |
|---|---|---|---|
| full | 2048 | False | 1.000 |
| h2o | 2048 | False | 0.100 |
| pyramidkv | 2048 | False | 0.100 |
| sage | 2048 | False | 0.200 |
| streamingllm | 2048 | False | 0.200 |
| full | 2048 | True | 1.000 |
| h2o | 2048 | True | 0.000 |
| pyramidkv | 2048 | True | 0.000 |
| sage | 2048 | True | 0.333 |
| sage-nodecay | 2048 | True | 0.667 |
