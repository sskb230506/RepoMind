import logging
import os

import tree_sitter_typescript
from tree_sitter import Language, Node, Parser

from ..types import ParsedSymbol, ParseResult, SymbolType
from .javascript import JavaScriptParser

logger = logging.getLogger(__name__)


class TypeScriptParser(JavaScriptParser):
    """
    Tree-sitter parser for TypeScript and TSX, extending JavaScriptParser
    with interfaces, enums, type aliases, and typed inheritance clauses.
    """

    def __init__(self) -> None:
        self._ts_language = Language(tree_sitter_typescript.language_typescript())
        self._tsx_language = Language(tree_sitter_typescript.language_tsx())

    @property
    def language_name(self) -> str:
        return "TypeScript"

    @property
    def supported_extensions(self) -> set[str]:
        return {".ts", ".tsx", ".mts", ".cts"}

    def get_tree_sitter_language(self) -> Language:
        return self._ts_language

    def get_parser_for_path(self, file_path: str) -> Parser:
        ext = os.path.splitext(file_path)[1].lower() if file_path else ""
        if ext == ".tsx":
            return Parser(self._tsx_language)
        return Parser(self._ts_language)

    def parse(self, code: str | bytes, file_path: str = "") -> ParseResult:
        """Override parse to use the TSX grammar when file ends with .tsx."""
        if not code:
            return ParseResult(language=self.language_name, symbols=[])

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
            return ParseResult(
                language=self.language_name,
                symbols=[],
                has_errors=True,
                error_message=f"Encoding error: {e}",
            )

        try:
            parser = self.get_parser_for_path(file_path)
            tree = parser.parse(code_bytes)
            if tree is None or tree.root_node is None:
                return ParseResult(
                    language=self.language_name,
                    symbols=[],
                    has_errors=True,
                    error_message="Empty syntax tree",
                )

            has_error = tree.root_node.has_error
            symbols = self.extract_symbols(tree.root_node, code_bytes, file_path)
            return ParseResult(
                language=self.language_name,
                symbols=symbols,
                has_errors=has_error,
                error_message="Syntax errors detected" if has_error else None,
            )
        except Exception as e:
            logger.warning("TypeScript parse failure: %s", e, exc_info=True)
            return ParseResult(
                language=self.language_name,
                symbols=[],
                has_errors=True,
                error_message=f"Parse failure: {e}",
            )

    def _walk_node(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        node_type = node.type

        # 1. Interface Declaration
        if node_type == "interface_declaration":
            self._handle_interface(node, code_bytes, symbols, scope_stack)
            return

        # 2. Type Alias Declaration
        if node_type == "type_alias_declaration":
            self._handle_type_alias(node, code_bytes, symbols, scope_stack)
            return

        # 3. Enum Declaration
        if node_type == "enum_declaration":
            self._handle_enum(node, code_bytes, symbols, scope_stack)
            return

        # Otherwise delegate to JavaScriptParser for standard JS constructs
        super()._walk_node(node, code_bytes, symbols, scope_stack)

    def _extract_class_heritage(
        self,
        heritage_node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        class_idx: int,
        class_qname: str,
    ) -> None:
        """Handle both extends_clause and implements_clause in TypeScript classes."""
        for child in heritage_node.children:
            if child.type == "extends_clause":
                for sub in child.children:
                    if sub.type in (
                        "identifier",
                        "type_identifier",
                        "member_expression",
                    ):
                        base_name = self.get_node_text(sub, code_bytes).strip()
                        c_start, c_end = self.get_node_lines(sub)
                        symbols.append(
                            ParsedSymbol(
                                symbol_type=SymbolType.INHERITANCE,
                                name=base_name,
                                qualified_name=f"{class_qname}.extends.{base_name}",
                                start_line=c_start,
                                end_line=c_end,
                                signature=f"extends {base_name}",
                                parent_index=class_idx,
                            )
                        )
            elif child.type == "implements_clause":
                for sub in child.children:
                    if sub.type in ("identifier", "type_identifier", "generic_type"):
                        iface_name = self.get_node_text(sub, code_bytes).strip()
                        c_start, c_end = self.get_node_lines(sub)
                        symbols.append(
                            ParsedSymbol(
                                symbol_type=SymbolType.INHERITANCE,
                                name=iface_name,
                                qualified_name=f"{class_qname}.implements.{iface_name}",
                                start_line=c_start,
                                end_line=c_end,
                                signature=f"implements {iface_name}",
                                parent_index=class_idx,
                            )
                        )
            elif child.type in ("identifier", "member_expression"):
                base_name = self.get_node_text(child, code_bytes).strip()
                c_start, c_end = self.get_node_lines(child)
                symbols.append(
                    ParsedSymbol(
                        symbol_type=SymbolType.INHERITANCE,
                        name=base_name,
                        qualified_name=f"{class_qname}.extends.{base_name}",
                        start_line=c_start,
                        end_line=c_end,
                        signature=f"extends {base_name}",
                        parent_index=class_idx,
                    )
                )

    def _handle_interface(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return

        iface_name = self.get_node_text(name_node, code_bytes).strip()
        start_line, end_line = self.get_node_lines(node)
        sig = self.get_signature_line(node, code_bytes)

        parent_idx = scope_stack[-1][0] if scope_stack else None
        parent_qname = scope_stack[-1][1] if scope_stack else None
        iface_qname = self.build_qualified_name(iface_name, parent_qname)

        iface_idx = len(symbols)
        symbols.append(
            ParsedSymbol(
                symbol_type=SymbolType.CLASS,
                name=iface_name,
                qualified_name=iface_qname,
                start_line=start_line,
                end_line=end_line,
                signature=sig,
                parent_index=parent_idx,
            )
        )

        # Check extends clause in interface
        for child in node.children:
            if child.type in ("extends_type_clause", "extends_clause"):
                for sub in child.children:
                    if sub.type in ("type_identifier", "identifier", "generic_type"):
                        base_name = self.get_node_text(sub, code_bytes).strip()
                        c_start, c_end = self.get_node_lines(sub)
                        symbols.append(
                            ParsedSymbol(
                                symbol_type=SymbolType.INHERITANCE,
                                name=base_name,
                                qualified_name=f"{iface_qname}.extends.{base_name}",
                                start_line=c_start,
                                end_line=c_end,
                                signature=f"extends {base_name}",
                                parent_index=iface_idx,
                            )
                        )

        # Walk interface body
        body_node = node.child_by_field_name("body")
        if body_node:
            scope_stack.append((iface_idx, iface_qname, "interface"))
            for child in body_node.children:
                if child.type == "method_signature":
                    m_name_node = child.child_by_field_name("name")
                    if m_name_node:
                        m_name = self.get_node_text(m_name_node, code_bytes).strip()
                        m_start, m_end = self.get_node_lines(child)
                        m_sig = self.get_signature_line(child, code_bytes)
                        symbols.append(
                            ParsedSymbol(
                                symbol_type=SymbolType.METHOD,
                                name=m_name,
                                qualified_name=f"{iface_qname}.{m_name}",
                                start_line=m_start,
                                end_line=m_end,
                                signature=m_sig,
                                parent_index=iface_idx,
                            )
                        )
                elif child.type == "property_signature":
                    p_name_node = child.child_by_field_name("name")
                    if p_name_node:
                        p_name = self.get_node_text(p_name_node, code_bytes).strip()
                        p_start, p_end = self.get_node_lines(child)
                        p_sig = self.get_signature_line(child, code_bytes)
                        symbols.append(
                            ParsedSymbol(
                                symbol_type=SymbolType.DEFINITION,
                                name=p_name,
                                qualified_name=f"{iface_qname}.{p_name}",
                                start_line=p_start,
                                end_line=p_end,
                                signature=p_sig,
                                parent_index=iface_idx,
                            )
                        )
            scope_stack.pop()

    def _handle_type_alias(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return

        name = self.get_node_text(name_node, code_bytes).strip()
        start_line, end_line = self.get_node_lines(node)
        sig = self.get_signature_line(node, code_bytes)

        parent_idx = scope_stack[-1][0] if scope_stack else None
        parent_qname = scope_stack[-1][1] if scope_stack else None
        qname = self.build_qualified_name(name, parent_qname)

        symbols.append(
            ParsedSymbol(
                symbol_type=SymbolType.DEFINITION,
                name=name,
                qualified_name=qname,
                start_line=start_line,
                end_line=end_line,
                signature=sig,
                parent_index=parent_idx,
            )
        )

    def _handle_enum(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return

        enum_name = self.get_node_text(name_node, code_bytes).strip()
        start_line, end_line = self.get_node_lines(node)
        sig = self.get_signature_line(node, code_bytes)

        parent_idx = scope_stack[-1][0] if scope_stack else None
        parent_qname = scope_stack[-1][1] if scope_stack else None
        enum_qname = self.build_qualified_name(enum_name, parent_qname)

        enum_idx = len(symbols)
        symbols.append(
            ParsedSymbol(
                symbol_type=SymbolType.DEFINITION,
                name=enum_name,
                qualified_name=enum_qname,
                start_line=start_line,
                end_line=end_line,
                signature=sig,
                parent_index=parent_idx,
            )
        )

        # Walk enum body members
        body_node = node.child_by_field_name("body")
        if body_node:
            for child in body_node.children:
                if child.type == "enum_assignment":
                    m_name_node = child.child_by_field_name("name")
                    if m_name_node:
                        m_name = self.get_node_text(m_name_node, code_bytes).strip()
                        m_start, m_end = self.get_node_lines(child)
                        symbols.append(
                            ParsedSymbol(
                                symbol_type=SymbolType.DEFINITION,
                                name=m_name,
                                qualified_name=f"{enum_qname}.{m_name}",
                                start_line=m_start,
                                end_line=m_end,
                                signature=self.get_signature_line(child, code_bytes),
                                parent_index=enum_idx,
                            )
                        )
                elif child.type == "property_identifier":
                    m_name = self.get_node_text(child, code_bytes).strip()
                    m_start, m_end = self.get_node_lines(child)
                    symbols.append(
                        ParsedSymbol(
                            symbol_type=SymbolType.DEFINITION,
                            name=m_name,
                            qualified_name=f"{enum_qname}.{m_name}",
                            start_line=m_start,
                            end_line=m_end,
                            signature=m_name,
                            parent_index=enum_idx,
                        )
                    )
