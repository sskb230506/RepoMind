import logging

import tree_sitter_python
from tree_sitter import Language, Node

from ..base import BaseLanguageParser
from ..types import ParsedSymbol, SymbolType

logger = logging.getLogger(__name__)


class PythonParser(BaseLanguageParser):
    """Tree-sitter parser for Python source code."""

    @property
    def language_name(self) -> str:
        return "Python"

    @property
    def supported_extensions(self) -> set[str]:
        return {".py", ".pyw", ".pyi"}

    def get_tree_sitter_language(self) -> Language:
        return Language(tree_sitter_python.language())

    def extract_symbols(
        self, root_node: Node, code_bytes: bytes, file_path: str
    ) -> list[ParsedSymbol]:
        symbols: list[ParsedSymbol] = []
        # Scope stack: tuple of (symbol_index, qualified_name, scope_kind)
        scope_stack: list[tuple[int, str, str]] = []

        self._walk_node(root_node, code_bytes, symbols, scope_stack)
        return symbols

    def _walk_node(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        node_type = node.type

        # 1. Imports
        if node_type == "import_statement":
            self._handle_import_statement(node, code_bytes, symbols, scope_stack)
            return

        if node_type == "import_from_statement":
            self._handle_import_from_statement(node, code_bytes, symbols, scope_stack)
            return

        # 2. Classes
        if node_type == "class_definition":
            self._handle_class_definition(node, code_bytes, symbols, scope_stack)
            return

        # 3. Functions & Methods
        if node_type == "function_definition":
            self._handle_function_definition(node, code_bytes, symbols, scope_stack)
            return

        # 4. Function Calls
        if node_type == "call":
            self._handle_call(node, code_bytes, symbols, scope_stack)

        # 5. Assignments (Definitions & Exports)
        if node_type in ("assignment", "augmented_assignment"):
            self._handle_assignment(node, code_bytes, symbols, scope_stack)

        # 6. Type Alias Statements (Python 3.12+)
        if node_type == "type_alias_statement":
            self._handle_type_alias(node, code_bytes, symbols, scope_stack)

        # Recurse through children
        for child in node.children:
            self._walk_node(child, code_bytes, symbols, scope_stack)

    def _handle_import_statement(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        start_line, end_line = self.get_node_lines(node)
        sig = self.get_signature_line(node, code_bytes)
        parent_idx = scope_stack[-1][0] if scope_stack else None

        for child in node.children:
            if child.type in ("dotted_name", "aliased_import"):
                name = self.get_node_text(child, code_bytes).strip()
                symbols.append(
                    ParsedSymbol(
                        symbol_type=SymbolType.IMPORT,
                        name=name,
                        qualified_name=name,
                        start_line=start_line,
                        end_line=end_line,
                        signature=sig,
                        parent_index=parent_idx,
                    )
                )

    def _handle_import_from_statement(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        start_line, end_line = self.get_node_lines(node)
        sig = self.get_signature_line(node, code_bytes)
        module_name_node = node.child_by_field_name("module_name")
        module_name = (
            self.get_node_text(module_name_node, code_bytes).strip()
            if module_name_node
            else ""
        )
        parent_idx = scope_stack[-1][0] if scope_stack else None

        # Look for imported names
        imported_names: list[str] = []
        for child in node.children:
            if child.type in ("dotted_name", "aliased_import", "identifier"):
                if child != module_name_node:
                    imported_names.append(self.get_node_text(child, code_bytes).strip())

        if not imported_names and module_name:
            symbols.append(
                ParsedSymbol(
                    symbol_type=SymbolType.IMPORT,
                    name=module_name,
                    qualified_name=module_name,
                    start_line=start_line,
                    end_line=end_line,
                    signature=sig,
                    parent_index=parent_idx,
                )
            )
        else:
            for item in imported_names:
                full_name = f"{module_name}.{item}" if module_name else item
                symbols.append(
                    ParsedSymbol(
                        symbol_type=SymbolType.IMPORT,
                        name=item,
                        qualified_name=full_name,
                        start_line=start_line,
                        end_line=end_line,
                        signature=sig,
                        parent_index=parent_idx,
                    )
                )

    def _handle_class_definition(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return

        class_name = self.get_node_text(name_node, code_bytes).strip()
        start_line, end_line = self.get_node_lines(node)
        sig = self.get_signature_line(node, code_bytes)

        parent_idx = scope_stack[-1][0] if scope_stack else None
        parent_qname = scope_stack[-1][1] if scope_stack else None
        class_qname = self.build_qualified_name(class_name, parent_qname)

        class_idx = len(symbols)
        symbols.append(
            ParsedSymbol(
                symbol_type=SymbolType.CLASS,
                name=class_name,
                qualified_name=class_qname,
                start_line=start_line,
                end_line=end_line,
                signature=sig,
                parent_index=parent_idx,
            )
        )

        # Inheritance relationships
        superclasses_node = node.child_by_field_name("superclasses")
        if not superclasses_node:
            # Fallback check for argument_list child
            for child in node.children:
                if child.type == "argument_list":
                    superclasses_node = child
                    break

        if superclasses_node:
            for child in superclasses_node.children:
                if child.type in ("identifier", "attribute"):
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

        # Recurse through class body inside new scope
        scope_stack.append((class_idx, class_qname, "class"))
        body_node = node.child_by_field_name("body")
        target_nodes = body_node.children if body_node else node.children
        for child in target_nodes:
            self._walk_node(child, code_bytes, symbols, scope_stack)
        scope_stack.pop()

    def _handle_function_definition(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return

        func_name = self.get_node_text(name_node, code_bytes).strip()
        start_line, end_line = self.get_node_lines(node)
        sig = self.get_signature_line(node, code_bytes)

        parent_idx = scope_stack[-1][0] if scope_stack else None
        parent_qname = scope_stack[-1][1] if scope_stack else None
        parent_kind = scope_stack[-1][2] if scope_stack else None

        is_method = parent_kind == "class"
        symbol_type = SymbolType.METHOD if is_method else SymbolType.FUNCTION
        func_qname = self.build_qualified_name(func_name, parent_qname)

        func_idx = len(symbols)
        symbols.append(
            ParsedSymbol(
                symbol_type=symbol_type,
                name=func_name,
                qualified_name=func_qname,
                start_line=start_line,
                end_line=end_line,
                signature=sig,
                parent_index=parent_idx,
            )
        )

        # Recurse through function body inside new scope
        scope_stack.append((func_idx, func_qname, "function"))
        body_node = node.child_by_field_name("body")
        target_nodes = body_node.children if body_node else node.children
        for child in target_nodes:
            self._walk_node(child, code_bytes, symbols, scope_stack)
        scope_stack.pop()

    def _handle_call(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        func_node = node.child_by_field_name("function")
        if not func_node:
            return

        call_name = self.get_node_text(func_node, code_bytes).strip()
        start_line, end_line = self.get_node_lines(node)
        sig = self.get_signature_line(node, code_bytes)

        parent_idx = scope_stack[-1][0] if scope_stack else None
        parent_qname = scope_stack[-1][1] if scope_stack else None
        call_qname = self.build_qualified_name(call_name, parent_qname)

        symbols.append(
            ParsedSymbol(
                symbol_type=SymbolType.CALL,
                name=call_name,
                qualified_name=call_qname,
                start_line=start_line,
                end_line=end_line,
                signature=sig,
                parent_index=parent_idx,
            )
        )

    def _handle_assignment(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        left_node = node.child_by_field_name("left")
        if not left_node:
            return

        target_name = self.get_node_text(left_node, code_bytes).strip()
        start_line, end_line = self.get_node_lines(node)
        sig = self.get_signature_line(node, code_bytes)

        # Special check for module-level `__all__` exports
        if target_name == "__all__":
            symbols.append(
                ParsedSymbol(
                    symbol_type=SymbolType.EXPORT,
                    name="__all__",
                    qualified_name="__all__",
                    start_line=start_line,
                    end_line=end_line,
                    signature=sig,
                    parent_index=None,
                )
            )
            # Also extract individual exported symbols from the list/tuple
            right_node = node.child_by_field_name("right")
            if right_node and right_node.type in ("list", "tuple"):
                for item in right_node.children:
                    if item.type == "string":
                        raw_str = self.get_node_text(item, code_bytes).strip()
                        clean_item = raw_str.strip("'\"")
                        symbols.append(
                            ParsedSymbol(
                                symbol_type=SymbolType.EXPORT,
                                name=clean_item,
                                qualified_name=clean_item,
                                start_line=start_line,
                                end_line=end_line,
                                signature=f"export {clean_item}",
                                parent_index=None,
                            )
                        )
            return

        # Variable / constant definition
        parent_idx = scope_stack[-1][0] if scope_stack else None
        parent_qname = scope_stack[-1][1] if scope_stack else None
        def_qname = self.build_qualified_name(target_name, parent_qname)

        symbols.append(
            ParsedSymbol(
                symbol_type=SymbolType.DEFINITION,
                name=target_name,
                qualified_name=def_qname,
                start_line=start_line,
                end_line=end_line,
                signature=sig,
                parent_index=parent_idx,
            )
        )

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
