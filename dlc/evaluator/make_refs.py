"""
Generate reference summaries for grader-selection so you don't hand-copy them.

For each (circuit, model) in REF_CIRCUITS x BENCH_MODELS it generates one L2
summary and writes a refs_template.json with summary_text filled and
manual_score = null. You then fill in your 0-100 grade for each, and feed that
file to grader_selection.

    uv run python -m dlc.evaluator.make_refs
    -> <OUTPUT_DIR>/refs_template.json   (hand-grade it, then run grader_selection)

Using a spread of models (weak..strong) is deliberate: it gives the range of
quality that makes the human-vs-grader correlation meaningful.
"""

from __future__ import annotations

import json
from pathlib import Path

from dlc.evaluator import config as C
from dlc.evaluator.benchmark import _facts_and_issues
from dlc.llm.explain import explain_circuit


def make_refs(progress=print) -> Path:
    if not C.REF_CIRCUITS:
        raise SystemExit("config.REF_CIRCUITS is empty - set BENCH_CIRCUITS first.")
    C.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    refs = []
    i = 0
    for path, good_goal, _wrong in C.REF_CIRCUITS:
        facts, issues = _facts_and_issues(path)
        for model in C.BENCH_MODELS:
            i += 1
            rid = f"r{i:02d}"
            summ = explain_circuit(facts=facts, issues=issues,
                                   test_summary=C.TEST_SUMMARY, student_goal=good_goal,
                                   model=model)
            text = summ.get("text") or ""
            refs.append({
                "ref_id": rid,
                "model": model,            
                "circuit_path": path,
                "student_goal": good_goal,
                "summary_text": text,
                "manual_score": None,       
            })
            progress(f"  {rid}  {model:<28} {Path(path).name:<28} "
                     f"{'ok' if text else 'EMPTY/gated - skip when grading'}")
    out = C.OUTPUT_DIR / "refs_template.json"
    out.write_text(json.dumps(refs, indent=2), encoding="utf-8")
    print(f"\n{len(refs)} reference summaries -> {out}")
    print("Next: open it, set each manual_score (0-100), delete any EMPTY/gated ones,")
    print("then: DLC_GRADER_REFS=<that file> uv run python -m dlc.evaluator.grader_selection")
    return out


if __name__ == "__main__":
    make_refs()
