import logging

import tree_sitter_java
from tree_sitter import Language, Node

from ..base import BaseLanguageParser
from ..types import ParsedSymbol, SymbolType

logger = logging.getLogger(__name__)


class JavaParser(BaseLanguageParser):
    """Tree-sitter parser for Java source code."""

    @property
    def language_name(self) -> str:
        return "Java"

    @property
    def supported_extensions(self) -> set[str]:
        return {".java"}

    def get_tree_sitter_language(self) -> Language:
        return Language(tree_sitter_java.language())

    def extract_symbols(
        self, root_node: Node, code_bytes: bytes, file_path: str
    ) -> list[ParsedSymbol]:
        symbols: list[ParsedSymbol] = []
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
        if node_type == "import_declaration":
            self._handle_import(node, code_bytes, symbols, scope_stack)
            return

        # 2. Module exports (module-info.java)
        if node_type == "exports_statement":
            self._handle_module_exports(node, code_bytes, symbols, scope_stack)
            return

        # 3. Classes, Interfaces, Enums, Records
        if node_type in (
            "class_declaration",
            "interface_declaration",
            "enum_declaration",
            "record_declaration",
        ):
            self._handle_class_or_interface(node, code_bytes, symbols, scope_stack)
            return

        # 4. Methods and Constructors
        if node_type in ("method_declaration", "constructor_declaration"):
            self._handle_method(node, code_bytes, symbols, scope_stack)
            return

        # 5. Field Definitions
        if node_type in ("field_declaration", "constant_declaration"):
            self._handle_field_declaration(node, code_bytes, symbols, scope_stack)
            return

        # 6. Enum Constants
        if node_type == "enum_constant":
            self._handle_enum_constant(node, code_bytes, symbols, scope_stack)
            return

        # 7. Method / Function Invocations
        if node_type in (
            "method_invocation",
            "explicit_constructor_invocation",
        ):
            self._handle_call(node, code_bytes, symbols, scope_stack)

        # Recurse through children
        for child in node.children:
            self._walk_node(child, code_bytes, symbols, scope_stack)

    def _handle_import(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        start_line, end_line = self.get_node_lines(node)
        sig = self.get_signature_line(node, code_bytes)
        parent_idx = scope_stack[-1][0] if scope_stack else None

        # Clean import name (e.g. 'java.util.List')
        text = self.get_node_text(node, code_bytes).strip()
        cleaned_name = (
            text.replace("import", "").replace("static", "").strip().rstrip(";")
        )

        symbols.append(
            ParsedSymbol(
                symbol_type=SymbolType.IMPORT,
                name=cleaned_name,
                qualified_name=cleaned_name,
                start_line=start_line,
                end_line=end_line,
                signature=sig,
                parent_index=parent_idx,
            )
        )

    def _handle_module_exports(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        start_line, end_line = self.get_node_lines(node)
        sig = self.get_signature_line(node, code_bytes)
        parent_idx = scope_stack[-1][0] if scope_stack else None
        text = self.get_node_text(node, code_bytes).strip()
        cleaned = text.replace("exports", "").strip().rstrip(";")

        symbols.append(
            ParsedSymbol(
                symbol_type=SymbolType.EXPORT,
                name=cleaned,
                qualified_name=cleaned,
                start_line=start_line,
                end_line=end_line,
                signature=sig,
                parent_index=parent_idx,
            )
        )

    def _is_public(self, node: Node, code_bytes: bytes) -> bool:
        modifiers_node = node.child_by_field_name("modifiers")
        if not modifiers_node:
            for child in node.children:
                if child.type == "modifiers":
                    modifiers_node = child
                    break
        if modifiers_node:
            for child in modifiers_node.children:
                if child.type == "public":
                    return True
        return False

    def _handle_class_or_interface(
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

        # Public classes in Java form the exported API
        if self._is_public(node, code_bytes):
            symbols.append(
                ParsedSymbol(
                    symbol_type=SymbolType.EXPORT,
                    name=class_name,
                    qualified_name=class_qname,
                    start_line=start_line,
                    end_line=end_line,
                    signature=f"public class {class_name}",
                    parent_index=class_idx,
                )
            )

        # Inheritance: superclass (extends Animal)
        superclass_node = node.child_by_field_name("superclass")
        if not superclass_node:
            for child in node.children:
                if child.type == "superclass":
                    superclass_node = child
                    break

        if superclass_node:
            for sub in superclass_node.children:
                if sub.type in ("type_identifier", "scoped_type_identifier"):
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

        # Inheritance: super_interfaces (implements ...) or extends_interfaces
        interfaces_node = node.child_by_field_name("interfaces")
        if not interfaces_node:
            for child in node.children:
                if child.type in ("super_interfaces", "extends_interfaces"):
                    interfaces_node = child
                    break

        if interfaces_node:
            is_extends = interfaces_node.type == "extends_interfaces"
            prefix = "extends" if is_extends else "implements"
            for sub in interfaces_node.children:
                if sub.type in ("type_identifier", "scoped_type_identifier"):
                    iface_name = self.get_node_text(sub, code_bytes).strip()
                    c_start, c_end = self.get_node_lines(sub)
                    symbols.append(
                        ParsedSymbol(
                            symbol_type=SymbolType.INHERITANCE,
                            name=iface_name,
                            qualified_name=f"{class_qname}.{prefix}.{iface_name}",
                            start_line=c_start,
                            end_line=c_end,
                            signature=f"{prefix} {iface_name}",
                            parent_index=class_idx,
                        )
                    )
                elif sub.type == "type_list":
                    for t in sub.children:
                        if t.type in ("type_identifier", "scoped_type_identifier"):
                            iface_name = self.get_node_text(t, code_bytes).strip()
                            c_start, c_end = self.get_node_lines(t)
                            symbols.append(
                                ParsedSymbol(
                                    symbol_type=SymbolType.INHERITANCE,
                                    name=iface_name,
                                    qualified_name=f"{class_qname}.{prefix}.{iface_name}",
                                    start_line=c_start,
                                    end_line=c_end,
                                    signature=f"{prefix} {iface_name}",
                                    parent_index=class_idx,
                                )
                            )

        # Walk class body
        body_node = node.child_by_field_name("body")
        if body_node:
            scope_stack.append((class_idx, class_qname, "class"))
            for child in body_node.children:
                self._walk_node(child, code_bytes, symbols, scope_stack)
            scope_stack.pop()

    def _handle_method(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        name_node = node.child_by_field_name("name")
        if not name_node:
            return

        method_name = self.get_node_text(name_node, code_bytes).strip()
        start_line, end_line = self.get_node_lines(node)
        sig = self.get_signature_line(node, code_bytes)

        parent_idx = scope_stack[-1][0] if scope_stack else None
        parent_qname = scope_stack[-1][1] if scope_stack else None
        method_qname = self.build_qualified_name(method_name, parent_qname)

        method_idx = len(symbols)
        symbols.append(
            ParsedSymbol(
                symbol_type=SymbolType.METHOD,
                name=method_name,
                qualified_name=method_qname,
                start_line=start_line,
                end_line=end_line,
                signature=sig,
                parent_index=parent_idx,
            )
        )

        if self._is_public(node, code_bytes):
            symbols.append(
                ParsedSymbol(
                    symbol_type=SymbolType.EXPORT,
                    name=method_name,
                    qualified_name=method_qname,
                    start_line=start_line,
                    end_line=end_line,
                    signature=sig,
                    parent_index=method_idx,
                )
            )

        body_node = node.child_by_field_name("body")
        if body_node:
            scope_stack.append((method_idx, method_qname, "method"))
            for child in body_node.children:
                self._walk_node(child, code_bytes, symbols, scope_stack)
            scope_stack.pop()

    def _handle_field_declaration(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        start_line, end_line = self.get_node_lines(node)
        sig = self.get_signature_line(node, code_bytes)
        parent_idx = scope_stack[-1][0] if scope_stack else None
        parent_qname = scope_stack[-1][1] if scope_stack else None

        for child in node.children:
            if child.type == "variable_declarator":
                name_node = child.child_by_field_name("name")
                if name_node:
                    name = self.get_node_text(name_node, code_bytes).strip()
                    symbols.append(
                        ParsedSymbol(
                            symbol_type=SymbolType.DEFINITION,
                            name=name,
                            qualified_name=self.build_qualified_name(
                                name, parent_qname
                            ),
                            start_line=start_line,
                            end_line=end_line,
                            signature=sig,
                            parent_index=parent_idx,
                        )
                    )

    def _handle_enum_constant(
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

        symbols.append(
            ParsedSymbol(
                symbol_type=SymbolType.DEFINITION,
                name=name,
                qualified_name=self.build_qualified_name(name, parent_qname),
                start_line=start_line,
                end_line=end_line,
                signature=sig,
                parent_index=parent_idx,
            )
        )

    def _handle_call(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        name_node = node.child_by_field_name("name")
        call_name = (
            self.get_node_text(name_node, code_bytes).strip()
            if name_node
            else self.get_node_text(node, code_bytes).split("(")[0].strip()
        )
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
