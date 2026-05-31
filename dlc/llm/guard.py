"""Prompt-leakage guard"""

import re


_LEAK_PATTERNS = [
    re.compile(r"(?i)^\s*you are\b.*assistant"),
    re.compile(r"(?i)^\s*system:\s*"),
    re.compile(r"(?i)^\s*\[circuit facts\]"),
    re.compile(r"(?i)^\s*\[test results\]"),
    re.compile(r"(?i)^\s*\[student goal\]"),
    re.compile(r"(?i)^\s*\[syllabus"),
    re.compile(r"(?i)^\s*rules:\s*$"),
    re.compile(r"(?i)ignore\s+(the\s+above|all\s+previous|previous\s+instructions)"),
    re.compile(r"(?i)^\s*write\s+six\s+paragraphs"),
]


def sanitize_output(text: str) -> str:
    if not text:
        return text
    out_lines = []
    for line in text.splitlines():
        if any(p.search(line) for p in _LEAK_PATTERNS):
            continue
        out_lines.append(line)
    return "\n".join(out_lines).strip()