"""graph_export edge widths must come from the single per-net width source."""

from dlc.parser.dig_parser import parse_dig_file
from dlc.parser.netlist import build_netlist
from dlc.parser.graph import build_signal_graph
from dlc.facts.net_width import infer_net_widths
from dlc.web.graph_export import to_cytoscape

_DIG = "data/sample_circuits/tier3_realistic/tier3_calculator.dig"


def _cy():
    c = parse_dig_file(_DIG)
    nl = build_netlist(c)
    g = build_signal_graph(c, nl)
    per_net, _ = infer_net_widths(c, nl)
    return c, nl, to_cytoscape(c, nl, g), per_net


def test_edge_bits_match_inferred_net_width():
    _c, _nl, cy, per_net = _cy()
    checked = 0
    for e in cy["edges"]:
        info = per_net.get(e["data"]["net_id"])
        if info is not None and info.width is not None:
            assert e["data"]["bits"] == info.width, e["data"]
            checked += 1
    assert checked > 0, "expected at least one width-known edge to verify"


def test_same_net_edges_report_one_consistent_width():
    _c, _nl, cy, _per_net = _cy()
    by_net: dict = {}
    for e in cy["edges"]:
        by_net.setdefault(e["data"]["net_id"], set()).add(e["data"]["bits"])
    for net_id, widths in by_net.items():
        assert len(widths) == 1, f"net {net_id} reported inconsistent widths {widths}"