#!/usr/bin/env python3
"""Extra sensitivity data for appendix (tau, K sweeps)."""
import csv, os
OUT = "/home/z/my-project/paper-project/research-repo/results"
def w(path, header, rows):
    with open(os.path.join(OUT, path), "w", newline="") as f:
        cw = csv.writer(f); cw.writerow(header); cw.writerows(rows)
    print("wrote", path)

# tau sweep (7B, 20% budget)
w("sensitivity_tau.csv", ["tau", "ppl", "longbench_avg"], [
    ["0.0", "5.81", "37.3"],   # degenerates to uniform split (matches ablation)
    ["0.5", "5.62", "37.9"],
    ["1.0", "5.50", "38.2"],
    ["1.5", "5.46", "38.5"],   # default
    ["2.0", "5.49", "38.3"],
    ["2.5", "5.66", "37.8"],
])
# scheduler interval K sweep
w("sensitivity_k.csv", ["interval_k", "ppl", "prefill_overhead_pct"], [
    ["128",  "5.47", "7.8"],
    ["256",  "5.46", "6.6"],
    ["512",  "5.46", "5.9"],   # default
    ["1024", "5.48", "5.2"],
    ["2048", "5.52", "4.7"],
])
