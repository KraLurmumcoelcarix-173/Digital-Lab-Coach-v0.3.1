from dlc.analyzer.wire_completeness import (
    Issue, IssueSeverity, IssueCollection, check_wire_completeness,
)
from dlc.analyzer.bit_widths import check_bit_widths
from dlc.analyzer.combinational_loops import check_combinational_loops

__all__ = [
    "Issue", "IssueSeverity", "IssueCollection",
    "check_wire_completeness", "check_bit_widths",
    "check_combinational_loops", "check_all_l1",
]


def check_all_l1(circuit):
    from dlc.parser.netlist import build_netlist
    from dlc.parser.graph import build_signal_graph
    from dlc.facts.extractor import extract_facts

    netlist = build_netlist(circuit)
    graph = build_signal_graph(circuit, netlist)
    facts = extract_facts(circuit, netlist=netlist, graph=graph)

    out = IssueCollection()
    out.extend(check_wire_completeness(
        circuit, netlist=netlist, graph=graph, facts=facts,
    ))
    out.extend(check_bit_widths(circuit, netlist=netlist, facts=facts))
    out.extend(check_combinational_loops(circuit, facts=facts))
    return out