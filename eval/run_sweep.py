# run_sweep.py
from __future__ import annotations
from eval_retrieval import eval_once

def sweep():
    configs = []

    for method in ["topk", "mmr"]:
        for top_k in [3, 5, 7]:
            if method == "topk":
                configs.append((method, top_k, 0, 0.0))
            else:
                for fetch_k in [30, 50, 80]:
                    for lam in [0.7, 0.8, 0.9, 0.95]:
                        configs.append((method, top_k, fetch_k, lam))

    results = []
    for method, top_k, fetch_k, lam in configs:
        r = eval_once(method=method, top_k=top_k, fetch_k=fetch_k or 25, lam=lam or 0.5)
        results.append((method, top_k, fetch_k, lam, r["hit@k"], r["mrr"]))

    # sort by hit@k then mrr
    results.sort(key=lambda x: (x[4], x[5]), reverse=True)

    print("method top_k fetch_k lam  hit@k   mrr")
    for row in results[:20]:
        print(f"{row[0]:5s} {row[1]:5d} {row[2]:7d} {row[3]:3.1f} {row[4]:6.3f} {row[5]:6.3f}")

if __name__ == "__main__":
    sweep()
