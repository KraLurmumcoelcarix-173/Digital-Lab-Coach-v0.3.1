"""
Grader-selection mini-benchmark.

Goal: pick the grader model whose scores correlate best with your manual
grades. You hand-grade ~20 reference L2 summaries; every candidate grader
then grades the same 20; we report the correlation per candidate.

Inputs: a JSON file (path in $DLC_GRADER_REFS) — a list of objects::

    [
      {"ref_id": "r01",
       "circuit_path": "/abs/path/to/circuit.dig",
       "summary_text": "the six paragraphs ...",
       "student_goal": null,
       "manual_score": 82},
      ... ~20 entries ...
    ]

Run::

    DLC_GRADER_REFS=/abs/refs.json uv run python -m dlc.evaluator.grader_selection

Writes a per-(ref, grader) CSV + prints a correlation ranking, all in
config.OUTPUT_DIR (outside the repo).
"""

from __future__ import annotations

import csv
import datetime as _dt
import json
import os
from pathlib import Path

from dlc.evaluator import config as C
from dlc.evaluator.benchmark import _facts_and_issues
from dlc.llm.grade import grade_summary

# Candidate graders to compare (default: the same 6 models under test).
CANDIDATE_GRADERS = list(C.BENCH_MODELS)


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return None
    return cov / (vx ** 0.5 * vy ** 0.5)


def _rank(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2:
        return None
    return _pearson(_rank(xs), _rank(ys))


def _mae(xs: list[float], ys: list[float]) -> float | None:
    if not xs:
        return None
    return sum(abs(x - y) for x, y in zip(xs, ys)) / len(xs)


def _load_refs() -> list[dict]:
    p = os.environ.get("DLC_GRADER_REFS")
    if not p:
        raise SystemExit("Set $DLC_GRADER_REFS to your references JSON file.")
    refs = json.loads(Path(p).read_text(encoding="utf-8"))
    if not refs:
        raise SystemExit("References file is empty.")
    return refs


def run_grader_selection(progress=print) -> Path:
    refs = _load_refs()
    C.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = C.OUTPUT_DIR / f"grader_selection_{stamp}.csv"

    # facts per circuit are reused across graders.
    facts_cache: dict[str, dict] = {}
    per_grader: dict[str, list[tuple[float, float]]] = {g: [] for g in CANDIDATE_GRADERS}

    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ref_id", "manual_score", "grader_model", "grader_score",
                    "grade_error"])
        for ref in refs:
            cp = ref["circuit_path"]
            if cp not in facts_cache:
                facts_cache[cp] = _facts_and_issues(cp)[0]
            facts = facts_cache[cp]
            manual = float(ref["manual_score"])
            for g in CANDIDATE_GRADERS:
                res = grade_summary(facts=facts, summary_text=ref["summary_text"],
                                    student_goal=ref.get("student_goal"),
                                    test_summary=None, grader_model=g)
                score = res.get("total")
                w.writerow([ref.get("ref_id", ""), manual, g,
                            score if score is not None else "",
                            res.get("error") or ""])
                fh.flush()
                if res.get("ok") and score is not None:
                    per_grader[g].append((manual, float(score)))
                progress(f"  {ref.get('ref_id','?')} | {g} -> {score}")

    print(f"\nRows -> {out}\n")
    print("Agreement with your manual grades (pick high pearson + spearman, LOW MAE):")
    print(f"  {'grader':<28}{'pearson':>9}{'spearman':>10}{'MAE':>8}{'n':>5}")

    def _fmt(v, d=3):
        return "n/a" if v is None else round(v, d)

    ranking = []
    for g, pairs in per_grader.items():
        hs = [m for m, _ in pairs]
        gs = [s for _, s in pairs]
        ranking.append((g, _pearson(hs, gs), _spearman(hs, gs), _mae(hs, gs), len(pairs)))
    for g, pr, sp, mae, n in sorted(ranking, key=lambda t: (t[1] is not None, t[1] or -2), reverse=True):
        print(f"  {g:<28}{str(_fmt(pr)):>9}{str(_fmt(sp)):>10}{str(_fmt(mae, 1)):>8}{n:>5}")
    return out


if __name__ == "__main__":
    run_grader_selection()
