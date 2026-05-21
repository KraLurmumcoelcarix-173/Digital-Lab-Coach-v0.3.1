"""
F4 : TestSpec extractor.

Given a parsed Circuit, walk its Testcase elements, parse the
`<dataString>` text into a structured `TestSpec` per testcase, and
match each header column to a top-level circuit port.
"""

from dataclasses import dataclass, field

from dlc.parser.models import Circuit


@dataclass(frozen=True)
class Token:

    raw: str
    kind: str            # "int" | "clock" | "highZ" | "dontcare" | "loop_expr" | "unknown"
    value: int | None    


@dataclass
class TestRow:
    __test__ = False

    raw: str
    values: list[Token] = field(default_factory=list)
    line_index: int = 0
    is_malformed: bool = False


@dataclass(frozen=True)
class VariableBinding:
    name: str
    role: str                       # "input" | "output" | "clock" | "unbound"
    component_index: int | None
    bit_width: int | None


@dataclass
class TestSpec:
    """One Testcase from a circuit, parsed into rows."""
    __test__ = False

    name: str                       
    component_index: int          
    headers: list[str]
    rows: list[TestRow]
    raw_data_string: str
    has_unexpanded_loops: bool

    def row_count(self) -> int:
        return len(self.rows)

    def well_formed_row_count(self) -> int:
        return sum(1 for r in self.rows if not r.is_malformed)

# Tokenization

def _tokenize(raw: str) -> Token:
    """Parse a single whitespace-stripped cell into a Token."""
    s = raw.strip()
    if not s:
        return Token(raw=s, kind="unknown", value=None)

    if s == "C":
        return Token(raw=s, kind="clock", value=None)
    if s in ("z", "Z"):
        return Token(raw=s, kind="highZ", value=None)
    if s in ("x", "X"):
        return Token(raw=s, kind="dontcare", value=None)

    # Parenthesized: 
    if s.startswith("(") and s.endswith(")") and len(s) >= 3:
        inner = s[1:-1].strip()
        try:
            return Token(raw=s, kind="int", value=int(inner))
        except ValueError:
            return Token(raw=s, kind="loop_expr", value=None)

    # Hex
    if len(s) > 2 and s[0] == "0" and s[1] in ("x", "X"):
        try:
            return Token(raw=s, kind="int", value=int(s, 16))
        except ValueError:
            return Token(raw=s, kind="unknown", value=None)

    # Binary
    if len(s) > 2 and s[0] == "0" and s[1] in ("b", "B"):
        try:
            return Token(raw=s, kind="int", value=int(s[2:], 2))
        except ValueError:
            return Token(raw=s, kind="unknown", value=None)

    # Plain decimal 
    try:
        return Token(raw=s, kind="int", value=int(s))
    except ValueError:
        return Token(raw=s, kind="unknown", value=None)



