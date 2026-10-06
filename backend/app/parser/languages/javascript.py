import logging

import tree_sitter_javascript
from tree_sitter import Language, Node

from ..base import BaseLanguageParser
from ..types import ParsedSymbol, SymbolType

logger = logging.getLogger(__name__)


class JavaScriptParser(BaseLanguageParser):
    """Tree-sitter parser for JavaScript (ESM, CommonJS, JSX)."""

    @property
    def language_name(self) -> str:
        return "JavaScript"

    @property
    def supported_extensions(self) -> set[str]:
        return {".js", ".jsx", ".mjs", ".cjs"}

    def get_tree_sitter_language(self) -> Language:
        return Language(tree_sitter_javascript.language())

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
        if node_type == "import_statement":
            self._handle_import_statement(node, code_bytes, symbols, scope_stack)
            return

        # 2. Exports
        if node_type == "export_statement":
            self._handle_export_statement(node, code_bytes, symbols, scope_stack)
            # Process declarations inside export (e.g. export class)
            for child in node.children:
                if child.type != "export":
                    self._walk_node(child, code_bytes, symbols, scope_stack)
            return

        # 3. Classes
        if node_type in ("class_declaration", "class"):
            self._handle_class(node, code_bytes, symbols, scope_stack)
            return

        # 4. Functions & Methods
        if node_type == "function_declaration":
            self._handle_function_declaration(node, code_bytes, symbols, scope_stack)
            return

        if node_type == "method_definition":
            self._handle_method_definition(node, code_bytes, symbols, scope_stack)
            return

        # 5. Variable Declarations (Functions or Definitions)
        if node_type in ("variable_declaration", "lexical_declaration"):
            self._handle_variable_declaration(node, code_bytes, symbols, scope_stack)
            # Recurse into initializers (e.g. arrow function bodies)
            for child in node.children:
                if child.type == "variable_declarator":
                    val_node = child.child_by_field_name("value")
                    if val_node and val_node.type in (
                        "arrow_function",
                        "function_expression",
                    ):
                        self._walk_function_body(
                            val_node, code_bytes, symbols, scope_stack
                        )
                    else:
                        for sub in child.children:
                            self._walk_node(sub, code_bytes, symbols, scope_stack)
            return

        # 6. Function Calls
        if node_type == "call_expression":
            self._handle_call_expression(node, code_bytes, symbols, scope_stack)

        # 7. CommonJS exports or assignments
        if node_type == "assignment_expression":
            self._handle_assignment_expression(node, code_bytes, symbols, scope_stack)

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

        source_node = node.child_by_field_name("source")
        source_text = (
            self.get_node_text(source_node, code_bytes).strip().strip("'\"")
            if source_node
            else ""
        )

        found_symbols = False
        for child in node.children:
            if child.type == "import_clause":
                for sub in child.children:
                    if sub.type == "identifier":
                        name = self.get_node_text(sub, code_bytes).strip()
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
                        found_symbols = True
                    elif sub.type == "named_imports":
                        for spec in sub.children:
                            if spec.type == "import_specifier":
                                alias = spec.child_by_field_name("alias")
                                target = alias or spec.child_by_field_name("name")
                                if target:
                                    name = self.get_node_text(
                                        target, code_bytes
                                    ).strip()
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
                                    found_symbols = True
                    elif sub.type == "namespace_import":
                        for sub_id in sub.children:
                            if sub_id.type == "identifier":
                                name = self.get_node_text(sub_id, code_bytes).strip()
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
                                found_symbols = True

        if not found_symbols and source_text:
            symbols.append(
                ParsedSymbol(
                    symbol_type=SymbolType.IMPORT,
                    name=source_text,
                    qualified_name=source_text,
                    start_line=start_line,
                    end_line=end_line,
                    signature=sig,
                    parent_index=parent_idx,
                )
            )

    def _handle_export_statement(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        start_line, end_line = self.get_node_lines(node)
        sig = self.get_signature_line(node, code_bytes)
        parent_idx = scope_stack[-1][0] if scope_stack else None

        export_names: list[str] = []

        # Check export clause e.g. export { a, b as c }
        for child in node.children:
            if child.type == "export_clause":
                for spec in child.children:
                    if spec.type == "export_specifier":
                        alias = spec.child_by_field_name("alias")
                        target = alias or spec.child_by_field_name("name")
                        if target:
                            export_names.append(
                                self.get_node_text(target, code_bytes).strip()
                            )
            elif child.type == "default":
                export_names.append("default")

        # Check declaration e.g. export const x = 10; export function foo()
        decl = node.child_by_field_name("declaration")
        if decl:
            name_node = decl.child_by_field_name("name")
            if name_node:
                export_names.append(self.get_node_text(name_node, code_bytes).strip())
            elif decl.type in ("variable_declaration", "lexical_declaration"):
                for c in decl.children:
                    if c.type == "variable_declarator":
                        var_id = c.child_by_field_name("name")
                        if var_id:
                            export_names.append(
                                self.get_node_text(var_id, code_bytes).strip()
                            )

        if not export_names:
            export_names.append("export")

        for name in export_names:
            symbols.append(
                ParsedSymbol(
                    symbol_type=SymbolType.EXPORT,
                    name=name,
                    qualified_name=name,
                    start_line=start_line,
                    end_line=end_line,
                    signature=sig,
                    parent_index=parent_idx,
                )
            )

    def _handle_class(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        name_node = node.child_by_field_name("name")
        class_name = (
            self.get_node_text(name_node, code_bytes).strip()
            if name_node
            else "AnonymousClass"
        )
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

        # Extract inheritance
        for child in node.children:
            if child.type == "class_heritage":
                self._extract_class_heritage(
                    child, code_bytes, symbols, class_idx, class_qname
                )

        # Walk class body
        body_node = node.child_by_field_name("body")
        if body_node:
            scope_stack.append((class_idx, class_qname, "class"))
            for child in body_node.children:
                self._walk_node(child, code_bytes, symbols, scope_stack)
            scope_stack.pop()

    def _extract_class_heritage(
        self,
        heritage_node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        class_idx: int,
        class_qname: str,
    ) -> None:
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

    def _handle_method_definition(
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

        body_node = node.child_by_field_name("body")
        if body_node:
            scope_stack.append((method_idx, method_qname, "method"))
            for child in body_node.children:
                self._walk_node(child, code_bytes, symbols, scope_stack)
            scope_stack.pop()

    def _handle_function_declaration(
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
        func_qname = self.build_qualified_name(func_name, parent_qname)

        func_idx = len(symbols)
        symbols.append(
            ParsedSymbol(
                symbol_type=SymbolType.FUNCTION,
                name=func_name,
                qualified_name=func_qname,
                start_line=start_line,
                end_line=end_line,
                signature=sig,
                parent_index=parent_idx,
            )
        )

        body_node = node.child_by_field_name("body")
        if body_node:
            scope_stack.append((func_idx, func_qname, "function"))
            for child in body_node.children:
                self._walk_node(child, code_bytes, symbols, scope_stack)
            scope_stack.pop()

    def _handle_variable_declaration(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        parent_idx = scope_stack[-1][0] if scope_stack else None
        parent_qname = scope_stack[-1][1] if scope_stack else None

        for child in node.children:
            if child.type == "variable_declarator":
                name_node = child.child_by_field_name("name")
                value_node = child.child_by_field_name("value")
                if not name_node:
                    continue

                var_name = self.get_node_text(name_node, code_bytes).strip()
                start_line, end_line = self.get_node_lines(child)
                sig = self.get_signature_line(child, code_bytes)
                var_qname = self.build_qualified_name(var_name, parent_qname)

                # If initialized with an arrow function or function expression
                if value_node and value_node.type in (
                    "arrow_function",
                    "function_expression",
                ):
                    symbols.append(
                        ParsedSymbol(
                            symbol_type=SymbolType.FUNCTION,
                            name=var_name,
                            qualified_name=var_qname,
                            start_line=start_line,
                            end_line=end_line,
                            signature=sig,
                            parent_index=parent_idx,
                        )
                    )
                else:
                    symbols.append(
                        ParsedSymbol(
                            symbol_type=SymbolType.DEFINITION,
                            name=var_name,
                            qualified_name=var_qname,
                            start_line=start_line,
                            end_line=end_line,
                            signature=sig,
                            parent_index=parent_idx,
                        )
                    )

    def _walk_function_body(
        self,
        func_node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        body = func_node.child_by_field_name("body")
        if body:
            last_idx = len(symbols) - 1
            last_qname = symbols[last_idx].qualified_name
            scope_stack.append((last_idx, last_qname, "function"))
            for c in body.children:
                self._walk_node(c, code_bytes, symbols, scope_stack)
            scope_stack.pop()

    def _handle_call_expression(
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

        # Special check for CommonJS require('...') imports
        if call_name == "require":
            args = node.child_by_field_name("arguments")
            arg_text = (
                self.get_node_text(args, code_bytes).strip().strip("()'\"")
                if args
                else ""
            )
            symbols.append(
                ParsedSymbol(
                    symbol_type=SymbolType.IMPORT,
                    name=arg_text or "require",
                    qualified_name=arg_text or "require",
                    start_line=start_line,
                    end_line=end_line,
                    signature=sig,
                    parent_index=parent_idx,
                )
            )
            return

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

    def _handle_assignment_expression(
        self,
        node: Node,
        code_bytes: bytes,
        symbols: list[ParsedSymbol],
        scope_stack: list[tuple[int, str, str]],
    ) -> None:
        left_node = node.child_by_field_name("left")
        if not left_node:
            return

        left_text = self.get_node_text(left_node, code_bytes).strip()
        start_line, end_line = self.get_node_lines(node)
        sig = self.get_signature_line(node, code_bytes)
        parent_idx = scope_stack[-1][0] if scope_stack else None

        # CommonJS export detection: module.exports or exports.foo
        if left_text.startswith("module.exports") or left_text.startswith("exports."):
            name = left_text.split(".")[-1]
            symbols.append(
                ParsedSymbol(
                    symbol_type=SymbolType.EXPORT,
                    name=name,
                    qualified_name=left_text,
                    start_line=start_line,
                    end_line=end_line,
                    signature=sig,
                    parent_index=parent_idx,
                )
            )
            return

        # Variable/property definition
        parent_qname = scope_stack[-1][1] if scope_stack else None
        symbols.append(
            ParsedSymbol(
                symbol_type=SymbolType.DEFINITION,
                name=left_text,
                qualified_name=self.build_qualified_name(left_text, parent_qname),
                start_line=start_line,
                end_line=end_line,
                signature=sig,
                parent_index=parent_idx,
            )
        )
