import logging
from abc import ABC, abstractmethod

from tree_sitter import Language, Node, Parser

from .types import ParsedSymbol, ParseResult

logger = logging.getLogger(__name__)


class BaseLanguageParser(ABC):
    """
    Abstract base class for Tree-sitter source code parsers.
    New languages should inherit from this class and register with ParserRegistry.
    """

    @property
    @abstractmethod
    def language_name(self) -> str:
        """Normalized language name, e.g. 'Python', 'JavaScript'."""
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> set[str]:
        """Set of supported file extensions with leading dot, e.g. {'.py'}."""
        pass

    @abstractmethod
    def get_tree_sitter_language(self) -> Language:
        """Return the Tree-sitter Language instance for this parser."""
        pass

    def get_parser(self) -> Parser:
        """Instantiate and configure the Tree-sitter Parser."""
        return Parser(self.get_tree_sitter_language())

    def parse(self, code: str | bytes, file_path: str = "") -> ParseResult:
        """
        Safely parse source code and extract all supported symbols.
        Guaranteed to fail gracefully without throwing unhandled exceptions.
        """
        if not code:
            return ParseResult(language=self.language_name, symbols=[])

        # 1. Ensure bytes encoding
        try:
            if isinstance(code, str):
                code_bytes = code.encode("utf-8", errors="replace")
            elif isinstance(code, bytes):
                code_bytes = code
            else:
                return ParseResult(
                    language=self.language_name,
                    symbols=[],
                    has_errors=True,
                    error_message=f"Invalid code input type: {type(code).__name__}",
                )
        except Exception as e:
            logger.warning("Failed to encode code for %s: %s", file_path, e)
            return ParseResult(
                language=self.language_name,
                symbols=[],
                has_errors=True,
                error_message=f"Encoding error: {e}",
            )

        # 2. Parse syntax tree with Tree-sitter
        try:
            parser = self.get_parser()
            tree = parser.parse(code_bytes)
            if tree is None or tree.root_node is None:
                return ParseResult(
                    language=self.language_name,
                    symbols=[],
                    has_errors=True,
                    error_message="Tree-sitter returned empty syntax tree.",
                )

            has_syntax_errors = tree.root_node.has_error

            # 3. Extract symbols from syntax tree
            symbols = self.extract_symbols(tree.root_node, code_bytes, file_path)

            return ParseResult(
                language=self.language_name,
                symbols=symbols,
                has_errors=has_syntax_errors,
                error_message=(
                    "Syntax errors detected in source code."
                    if has_syntax_errors
                    else None
                ),
            )
        except Exception as e:
            logger.warning(
                "Tree-sitter parser exception for %s (%s): %s",
                file_path,
                self.language_name,
                e,
                exc_info=True,
            )
            return ParseResult(
                language=self.language_name,
                symbols=[],
                has_errors=True,
                error_message=f"Parse failure: {e}",
            )

    @abstractmethod
    def extract_symbols(
        self, root_node: Node, code_bytes: bytes, file_path: str
    ) -> list[ParsedSymbol]:
        """
        Extract functions, methods, classes, imports, exports, function calls,
        inheritance relationships, and definitions from the AST.
        """
        pass

    # Utility helpers for subclasses
    def get_node_text(self, node: Node, code_bytes: bytes) -> str:
        """Return the decoded text slice corresponding to the AST node."""
        return code_bytes[node.start_byte : node.end_byte].decode(
            "utf-8", errors="replace"
        )

    def get_node_lines(self, node: Node) -> tuple[int, int]:
        """Return 1-indexed (start_line, end_line) line numbers."""
        return node.start_point.row + 1, node.end_point.row + 1

    def get_signature_line(
        self, node: Node, code_bytes: bytes, max_len: int = 250
    ) -> str:
        """Extract the first line / signature declaration of a node."""
        text = self.get_node_text(node, code_bytes).strip()
        first_line = text.split("\n")[0].strip()
        if len(first_line) > max_len:
            return first_line[:max_len] + "..."
        return first_line

    def build_qualified_name(self, name: str, parent_qname: str | None = None) -> str:
        """Build a hierarchical qualified name (e.g. 'Class.method')."""
        if parent_qname:
            return f"{parent_qname}.{name}"
        return name
