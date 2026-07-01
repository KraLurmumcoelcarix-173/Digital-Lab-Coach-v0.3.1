"""/api/simulate returns per-net signal-flow values for a clicked test row,
plus expected-vs-found for the top-level outputs (so a failed row renders red).
Purely additive endpoint — it never invokes Digital.
"""

from fastapi.testclient import TestClient

from dlc.web.server import app

client = TestClient(app)

_BASE = "data/sample_circuits"


def _upload(paths: list[str]) -> str:
    files = []
    for p in paths:
        files.append(("files", (p.split("/")[-1], open(p, "rb"), "application/xml")))
    r = client.post("/api/circuit", files=files)
    assert r.status_code == 200
    return r.json()["session_id"]


def test_simulate_combinational_calculator_with_subcircuit():
    sid = _upload([
        f"{_BASE}/tier3_realistic/tier3_calculator.dig",
        f"{_BASE}/tier3_realistic/bool_unit.dig",
    ])
    r = client.post("/api/simulate", json={
        "session_id": sid, "filename": "tier3_calculator.dig",
        "spec_index": 0, "row_index": 0,
    }).json()
    assert r["ok"] is True
    # every net carries a value (subcircuit resolved), nothing unresolved
    assert r["net_values"], r
    assert r["unresolved_nets"] == []
    result = next(o for o in r["outputs"] if o["label"] == "Result")
    assert result["expected"] == 8 and result["found"] == 8 and result["ok"] is True
    # a net value payload is shaped for the UI
    any_net = next(iter(r["net_values"].values()))
    assert set(any_net) == {"value", "bits", "hex"}


def test_simulate_failed_row_reports_expected_vs_found():
    sid = _upload([f"{_BASE}/30_bug_benchmark/bug3_wrong_cin/Wrong_cin.dig"])
    # third good row expects Sum=7; the buggy circuit actually yields 8
    r = client.post("/api/simulate", json={
        "session_id": sid, "filename": "Wrong_cin.dig",
        "spec_index": 0, "row_index": 2,
    }).json()
    assert r["ok"] is True
    sumo = next(o for o in r["outputs"] if o["label"] == "Sum")
    assert sumo["expected"] == 7
    assert sumo["found"] == 8
    assert sumo["ok"] is False


def test_simulate_bad_session_is_404():
    r = client.post("/api/simulate", json={
        "session_id": "nope", "filename": "x.dig",
        "spec_index": 0, "row_index": 0,
    })
    assert r.status_code == 404
