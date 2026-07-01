"""Deterministic circuit value evaluator (Layer-1 UI signal-flow).

Digital's `CLI test -verbose` only reports a testcase's declared I/O columns,
never interior net values. To color interior wires with the value they carry
when a test row is clicked, we compute those values ourselves.

`simulate()` runs a purely *combinational* fixpoint: it seeds the top-level
inputs (and constants) with a row's values and propagates through every gate,
mux, decoder, splitter, adder, comparator and resolved subcircuit until no net
changes. Sequential/stateful parts (Register, Clock-driven feedback) and a few
components whose exact semantics we don't yet model (BarrelShifter, ROM,
sign-extend) are left *unresolved* on purpose — the UI shows no value there
rather than a wrong one.

This module is additive: it never touches the Layer-1 checkers.
"""

from dlc.sim.simulator import (
    SimResult,
    simulate,
    simulate_sequential,
    inputs_for_row,
)


__all__ = ["SimResult", "simulate", "simulate_sequential", "inputs_for_row"]
