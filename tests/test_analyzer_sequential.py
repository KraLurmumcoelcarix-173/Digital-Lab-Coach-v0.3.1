import glob

from dlc.analyzer import check_all_l1
from dlc.analyzer.sequential import check_sequential
from dlc.analyzer.wire_completeness import IssueSeverity
from dlc.parser.dig_parser import parse_dig_file
from dlc.parser.models import Circuit, Component, Position


def _rom(idx_label: str, data: str | None) -> Component:
    attrs: dict = {"Label": idx_label}
    if data is not None:
        attrs["Data"] = data
    return Component(
        element_name="ROM",
        position=Position(0, 0),
        attributes=attrs,
        label=idx_label,
    )


def test_empty_rom_flagged_as_warning():
    c = Circuit(
        format_version=2,
        components=[
            _rom("empty", None),
            _rom("filled", "82,86,80,81"),
        ],
        wires=[],
        source_path="synthetic",
    )
    issues = check_sequential(c)
    empties = issues.by_kind("empty_rom")
    assert len(empties) == 1
    assert empties[0].severity == IssueSeverity.WARNING
    assert empties[0].component_indices == [0]
    assert "no data" in empties[0].title.lower()


def test_empty_string_data_also_flagged():
    c = Circuit(
        format_version=2,
        components=[_rom("blank_string", "")],
        wires=[],
        source_path="synthetic",
    )
    issues = check_sequential(c)
    assert len(issues.by_kind("empty_rom")) == 1


def test_whitespace_only_data_treated_as_empty():
    c = Circuit(
        format_version=2,
        components=[_rom("spaces", "   \n\t  ")],
        wires=[],
        source_path="synthetic",
    )
    issues = check_sequential(c)
    assert len(issues.by_kind("empty_rom")) == 1


def test_populated_rom_not_flagged():
    c = Circuit(
        format_version=2,
        components=[_rom("good", "1,a")],
        wires=[],
        source_path="synthetic",
    )
    issues = check_sequential(c)
    assert len(issues.by_kind("empty_rom")) == 0


def test_aggregator_includes_empty_rom_kind():
    c = Circuit(
        format_version=2,
        components=[_rom("empty", None)],
        wires=[],
        source_path="synthetic",
    )
    issues = check_all_l1(c)
    assert len(issues.by_kind("empty_rom")) == 1


def test_no_false_positives_on_shipped_samples():
    for f in glob.glob("data/sample_circuits/**/*.dig", recursive=True):
        c = parse_dig_file(f)
        issues = check_sequential(c)
        empties = issues.by_kind("empty_rom")
        assert empties == [], f"{f}: unexpected empty_rom flag {empties}"