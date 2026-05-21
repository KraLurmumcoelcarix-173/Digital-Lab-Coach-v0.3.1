"""
Tests for dlc.testing.results
"""

from dlc.testing.results import (
    parse_cli_output,
    TestcaseResult,
    TestRunResults,
)


def test_parse_single_pass_line():
    res = parse_cli_output("cpu: passed\n")
    assert len(res.testcases) == 1
    tc = res.testcases[0]
    assert tc.name == "cpu"
    assert tc.status == "passed"
    assert tc.fail_pct is None


def test_parse_single_fail_line_with_percent():
    res = parse_cli_output("cpu: failed (60%)\n")
    assert len(res.testcases) == 1
    tc = res.testcases[0]
    assert tc.name == "cpu"
    assert tc.status == "failed"
    assert tc.fail_pct == 60


def test_parse_single_fail_line_without_percent():
    """Some Digital versions or summary lines emit 'failed' with no %."""
    res = parse_cli_output("ALU: failed\n")
    assert len(res.testcases) == 1
    assert res.testcases[0].status == "failed"
    assert res.testcases[0].fail_pct is None


def test_parse_empty_output():
    res = parse_cli_output("")
    assert res.testcases == []
    assert res.raw_output == ""


def test_parse_blank_lines_only():
    res = parse_cli_output("\n   \n\n")
    assert res.testcases == []


def test_parse_multiple_testcases():
    text = "add-sub: passed\nALU: failed (33%)\nslt-unit: passed\n"
    res = parse_cli_output(text)
    assert len(res.testcases) == 3
    by_name = res.by_name()
    assert by_name["add-sub"].status == "passed"
    assert by_name["ALU"].status == "failed"
    assert by_name["ALU"].fail_pct == 33
    assert by_name["slt-unit"].status == "passed"


def test_duplicate_name_last_occurrence_wins():
    """Autograder re-runs the same Testcase; the later result should
    overwrite the earlier one."""
    text = "cpu: failed (50%)\ncpu: passed\n"
    res = parse_cli_output(text)
    assert len(res.testcases) == 1
    assert res.testcases[0].status == "passed"


def test_parse_handles_java_log_noise_around_result():
    text = (
        "lab5 lab5.zip Running basic test   Using circuit: cpu.dig "
        "(student submission)   Using tests  : "
        "/autograder/source/../submission/lab5/cpu_basic_TEST.dig "
        "(from /autograder/source/tests/basic.txt)\n"
        "Apr 30, 2026 7:37:23 PM java.util.prefs.FileSystemPreferences$1 run\n"
        "INFO: Created user preferences directory.\n"
        "cpu: passed\n"
    )
    res = parse_cli_output(text)
    assert len(res.testcases) == 1
    assert res.testcases[0].name == "cpu"
    assert res.testcases[0].status == "passed"


def test_lines_with_colons_but_not_results_are_ignored():
    text = (
        "INFO: Created user preferences directory.\n"
        "Using circuit: cpu.dig (student submission)\n"
        "Using tests  : path/to/foo.txt\n"
    )
    res = parse_cli_output(text)
    assert res.testcases == []

# Helpers

def test_by_name_returns_dict_keyed_by_testcase_name():
    res = parse_cli_output("add-sub: passed\nALU: failed (10%)\n")
    by_name = res.by_name()
    assert isinstance(by_name, dict)
    assert set(by_name.keys()) == {"add-sub", "ALU"}

def test_failed_returns_only_failed_testcases():
    res = parse_cli_output("a: passed\nb: failed (20%)\nc: failed\n")
    failed = res.failed()
    assert len(failed) == 2
    assert {t.name for t in failed} == {"b", "c"}

def test_passed_testcases_returns_only_passing():
    res = parse_cli_output("a: passed\nb: failed (20%)\nc: passed\n")
    passing = res.passed_testcases()
    assert len(passing) == 2
    assert {t.name for t in passing} == {"a", "c"}

def test_name_with_hyphen_recognized():
    res = parse_cli_output("add-sub: passed\n")
    assert len(res.testcases) == 1
    assert res.testcases[0].name == "add-sub"

def test_name_with_dot_recognized():
    res = parse_cli_output("lab3.1: passed\n")
    assert len(res.testcases) == 1
    assert res.testcases[0].name == "lab3.1"

def test_trailing_whitespace_tolerated():
    res = parse_cli_output("cpu: passed   \n")
    assert len(res.testcases) == 1
    assert res.testcases[0].status == "passed"

def test_raw_output_preserved_for_l3_context():
    text = "noise line\ncpu: failed (20%)\nmore noise\n"
    res = parse_cli_output(text)
    assert res.raw_output == text
