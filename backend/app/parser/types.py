from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class SymbolType(StrEnum):
    """Types of source code symbols extracted by the parser subsystem."""

    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"
    IMPORT = "import"
    EXPORT = "export"
    CALL = "call"
    INHERITANCE = "inheritance"
    DEFINITION = "definition"


@dataclass
class ParsedSymbol:
    """
    Represents an extracted source code symbol before database persistence.

    Attributes:
        symbol_type: Type of symbol (function, method, class, etc.).
        name: Short name of the symbol (e.g. 'calculate', 'UserService').
        qualified_name: Hierarchical path (e.g. 'UserService.getName').
        start_line: 1-indexed starting line.
        end_line: 1-indexed ending line.
        signature: Text signature or single-line declaration.
        parent_index: Index in the parent list (used to link parent_symbol_id).
        metadata: Extra language context (e.g. access modifiers, return types).
    """

    symbol_type: SymbolType | str
    name: str
    qualified_name: str
    start_line: int
    end_line: int
    signature: str | None = None
    parent_index: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParseResult:
    """Result of parsing source code with a language-aware parser."""

    language: str
    symbols: list[ParsedSymbol] = field(default_factory=list)
    has_errors: bool = False
    error_message: str | None = None
