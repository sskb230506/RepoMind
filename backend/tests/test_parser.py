from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

try:
    from backend.app.main import app
    from backend.app.models.repository import Repository, RepositoryStatus
    from backend.app.models.repository_file import RepositoryFile
    from backend.app.models.symbol import Symbol
    from backend.app.parser import (
        BaseLanguageParser,
        ParsedSymbol,
        ParserRegistry,
        SymbolType,
        get_parser_for_extension,
        get_parser_for_file,
        get_parser_for_language,
    )
    from backend.app.parser.languages.java import JavaParser
    from backend.app.parser.languages.javascript import JavaScriptParser
    from backend.app.parser.languages.python import PythonParser
    from backend.app.parser.languages.typescript import TypeScriptParser
    from backend.app.services.symbol_service import (
        parse_and_store_file_symbols,
        parse_source_code,
    )
except ModuleNotFoundError:
    from app.main import app
    from app.models.repository import Repository, RepositoryStatus
    from app.models.repository_file import RepositoryFile
    from app.models.symbol import Symbol
    from app.parser import (
        BaseLanguageParser,
        ParsedSymbol,
        ParserRegistry,
        SymbolType,
        get_parser_for_extension,
        get_parser_for_file,
        get_parser_for_language,
    )
    from app.parser.languages.java import JavaParser
    from app.parser.languages.javascript import JavaScriptParser
    from app.parser.languages.python import PythonParser
    from app.parser.languages.typescript import TypeScriptParser
    from app.services.symbol_service import (
        parse_and_store_file_symbols,
        parse_source_code,
    )

client = TestClient(app)


# -------------------------------------------------------------------------
# 1. Python Parser Tests
# -------------------------------------------------------------------------
class TestPythonParser:
    """Verifies symbol extraction for Python source files."""

    PYTHON_FIXTURE = """
__all__ = ["Animal", "calculate"]

import os
from math import sqrt

PI = 3.14159

class Animal(Creature):
    SPECIES = "mammal"

    def __init__(self, name: str):
        self.name = name

    def speak(self):
        print(self.name)

def calculate(a, b):
    result = a + b
    speak()
    return result
"""

    def test_extract_all_python_categories(self):
        parser = PythonParser()
        result = parser.parse(self.PYTHON_FIXTURE, "test.py")

        assert result.has_errors is False
        assert result.language == "Python"

        types_present = {s.symbol_type for s in result.symbols}
        assert SymbolType.CLASS in types_present
        assert SymbolType.INHERITANCE in types_present
        assert SymbolType.METHOD in types_present
        assert SymbolType.FUNCTION in types_present
        assert SymbolType.IMPORT in types_present
        assert SymbolType.EXPORT in types_present
        assert SymbolType.CALL in types_present
        assert SymbolType.DEFINITION in types_present

        # Verify Class & Inheritance
        classes = [s for s in result.symbols if s.symbol_type == SymbolType.CLASS]
        assert any(c.name == "Animal" for c in classes)

        inheritances = [
            s for s in result.symbols if s.symbol_type == SymbolType.INHERITANCE
        ]
        assert any(
            i.name == "Creature" and "extends Creature" in i.signature
            for i in inheritances
        )

        # Verify Methods & Parent Hierarchy
        methods = [s for s in result.symbols if s.symbol_type == SymbolType.METHOD]
        method_names = {m.name for m in methods}
        assert "__init__" in method_names
        assert "speak" in method_names
        speak_sym = next(m for m in methods if m.name == "speak")
        assert speak_sym.qualified_name == "Animal.speak"
        assert speak_sym.parent_index is not None

        # Verify Function
        functions = [s for s in result.symbols if s.symbol_type == SymbolType.FUNCTION]
        assert any(f.name == "calculate" for f in functions)

        # Verify Imports
        imports = [s for s in result.symbols if s.symbol_type == SymbolType.IMPORT]
        import_names = {i.name for i in imports}
        assert "os" in import_names
        assert "sqrt" in import_names

        # Verify Exports
        exports = [s for s in result.symbols if s.symbol_type == SymbolType.EXPORT]
        export_names = {e.name for e in exports}
        assert "__all__" in export_names
        assert "Animal" in export_names
        assert "calculate" in export_names

        # Verify Calls
        calls = [s for s in result.symbols if s.symbol_type == SymbolType.CALL]
        call_names = {c.name for c in calls}
        assert "print" in call_names
        assert "speak" in call_names

        # Verify Definitions
        definitions = [
            s for s in result.symbols if s.symbol_type == SymbolType.DEFINITION
        ]
        def_names = {d.name for d in definitions}
        assert "PI" in def_names
        assert "SPECIES" in def_names


# -------------------------------------------------------------------------
# 2. JavaScript Parser Tests
# -------------------------------------------------------------------------
class TestJavaScriptParser:
    """Verifies symbol extraction for JavaScript files."""

    JS_FIXTURE = """
import { helper } from './utils';
const external = require('external-pkg');

const MAX_LIMIT = 100;
export const VERSION = '1.0';

export class UserService extends BaseService {
    constructor(name) {
        super(name);
        this.name = name;
    }

    getName() {
        console.log(this.name);
        return this.name;
    }
}

function process(data) {
    helper(data);
    return data;
}

const compute = (x) => x * 2;

module.exports = { UserService, process };
"""

    def test_extract_all_javascript_categories(self):
        parser = JavaScriptParser()
        result = parser.parse(self.JS_FIXTURE, "service.js")

        assert result.has_errors is False
        assert result.language == "JavaScript"

        types_present = {s.symbol_type for s in result.symbols}
        assert SymbolType.CLASS in types_present
        assert SymbolType.INHERITANCE in types_present
        assert SymbolType.METHOD in types_present
        assert SymbolType.FUNCTION in types_present
        assert SymbolType.IMPORT in types_present
        assert SymbolType.EXPORT in types_present
        assert SymbolType.CALL in types_present
        assert SymbolType.DEFINITION in types_present

        # Verify Class and Inheritance
        classes = [s for s in result.symbols if s.symbol_type == SymbolType.CLASS]
        assert any(c.name == "UserService" for c in classes)

        inheritances = [
            s for s in result.symbols if s.symbol_type == SymbolType.INHERITANCE
        ]
        assert any(i.name == "BaseService" for i in inheritances)

        # Verify Methods
        methods = [s for s in result.symbols if s.symbol_type == SymbolType.METHOD]
        method_names = {m.name for m in methods}
        assert "constructor" in method_names
        assert "getName" in method_names

        # Verify Functions
        functions = [s for s in result.symbols if s.symbol_type == SymbolType.FUNCTION]
        func_names = {f.name for f in functions}
        assert "process" in func_names
        assert "compute" in func_names

        # Verify Imports (both ESM and CommonJS require)
        imports = [s for s in result.symbols if s.symbol_type == SymbolType.IMPORT]
        import_names = {i.name for i in imports}
        assert "helper" in import_names
        assert "external-pkg" in import_names

        # Verify Exports
        exports = [s for s in result.symbols if s.symbol_type == SymbolType.EXPORT]
        export_names = {e.name for e in exports}
        assert "VERSION" in export_names
        assert "exports" in export_names or "UserService" in export_names

        # Verify Calls
        calls = [s for s in result.symbols if s.symbol_type == SymbolType.CALL]
        call_names = {c.name for c in calls}
        assert "super" in call_names
        assert "console.log" in call_names
        assert "helper" in call_names

        # Verify Definitions
        definitions = [
            s for s in result.symbols if s.symbol_type == SymbolType.DEFINITION
        ]
        def_names = {d.name for d in definitions}
        assert "MAX_LIMIT" in def_names


# -------------------------------------------------------------------------
# 3. TypeScript Parser Tests
# -------------------------------------------------------------------------
class TestTypeScriptParser:
    """Verifies symbol extraction for TypeScript and TSX files."""

    TS_FIXTURE = """
import { IConfig } from './config';

export interface IAuthService extends IBaseAuth {
    login(u: string, p: string): boolean;
    token: string;
}

export enum Role {
    ADMIN = 1,
    USER = 2
}

export type Status = 'active' | 'inactive';

export class AuthManager extends BaseManager implements IAuthService {
    public token: string = 'xyz';

    public login(u: string, p: string): boolean {
        validate(u);
        return true;
    }
}

export const renderButton = () => {
    return true;
};
"""

    def test_extract_all_typescript_categories(self):
        parser = TypeScriptParser()
        result = parser.parse(self.TS_FIXTURE, "auth.ts")

        assert result.has_errors is False
        assert result.language == "TypeScript"

        types_present = {s.symbol_type for s in result.symbols}
        assert SymbolType.CLASS in types_present
        assert SymbolType.INHERITANCE in types_present
        assert SymbolType.METHOD in types_present
        assert SymbolType.FUNCTION in types_present
        assert SymbolType.IMPORT in types_present
        assert SymbolType.EXPORT in types_present
        assert SymbolType.CALL in types_present
        assert SymbolType.DEFINITION in types_present

        # Interface & Class
        classes = [s for s in result.symbols if s.symbol_type == SymbolType.CLASS]
        class_names = {c.name for c in classes}
        assert "IAuthService" in class_names
        assert "AuthManager" in class_names

        # Inheritance (extends and implements)
        inheritances = [
            s for s in result.symbols if s.symbol_type == SymbolType.INHERITANCE
        ]
        inherit_names = {i.name for i in inheritances}
        assert "IBaseAuth" in inherit_names
        assert "BaseManager" in inherit_names
        assert "IAuthService" in inherit_names

        # Enum and Type Alias Definitions
        definitions = [
            s for s in result.symbols if s.symbol_type == SymbolType.DEFINITION
        ]
        def_names = {d.name for d in definitions}
        assert "Role" in def_names
        assert "ADMIN" in def_names
        assert "Status" in def_names

        # Method and Function
        methods = [s for s in result.symbols if s.symbol_type == SymbolType.METHOD]
        assert any(m.name == "login" for m in methods)

        functions = [s for s in result.symbols if s.symbol_type == SymbolType.FUNCTION]
        assert any(f.name == "renderButton" for f in functions)

        # Call
        calls = [s for s in result.symbols if s.symbol_type == SymbolType.CALL]
        assert any(c.name == "validate" for c in calls)

    def test_tsx_component_parsing(self):
        parser = TypeScriptParser()
        tsx_fixture = """
import React from 'react';

export const MyComponent: React.FC = () => {
    handleClick();
    return <div>Hello</div>;
};
"""
        result = parser.parse(tsx_fixture, "component.tsx")
        assert result.has_errors is False
        assert any(s.name == "MyComponent" for s in result.symbols)
        assert any(s.name == "handleClick" for s in result.symbols)


# -------------------------------------------------------------------------
# 4. Java Parser Tests
# -------------------------------------------------------------------------
class TestJavaParser:
    """Verifies symbol extraction for Java source files."""

    JAVA_FIXTURE = """
package com.example.service;

import java.util.List;
import java.io.Serializable;

public class Dog extends Animal implements Pet, Serializable {
    public static final int MAX_AGE = 20;
    private String name;

    public Dog(String name) {
        super(name);
        this.name = name;
    }

    public void bark(int times) {
        System.out.println("Woof");
        recordSound(times);
    }
}
"""

    def test_extract_all_java_categories(self):
        parser = JavaParser()
        result = parser.parse(self.JAVA_FIXTURE, "Dog.java")

        assert result.has_errors is False
        assert result.language == "Java"

        types_present = {s.symbol_type for s in result.symbols}
        assert SymbolType.CLASS in types_present
        assert SymbolType.INHERITANCE in types_present
        assert SymbolType.METHOD in types_present
        assert SymbolType.IMPORT in types_present
        assert SymbolType.EXPORT in types_present
        assert SymbolType.CALL in types_present
        assert SymbolType.DEFINITION in types_present

        # Class & Interfaces
        classes = [s for s in result.symbols if s.symbol_type == SymbolType.CLASS]
        assert any(c.name == "Dog" for c in classes)

        # Inheritance (superclass + interfaces)
        inheritances = [
            s for s in result.symbols if s.symbol_type == SymbolType.INHERITANCE
        ]
        inherit_names = {i.name for i in inheritances}
        assert "Animal" in inherit_names
        assert "Pet" in inherit_names
        assert "Serializable" in inherit_names

        # Constructor and Method
        methods = [s for s in result.symbols if s.symbol_type == SymbolType.METHOD]
        method_names = {m.name for m in methods}
        assert "Dog" in method_names
        assert "bark" in method_names

        # Public Exports
        exports = [s for s in result.symbols if s.symbol_type == SymbolType.EXPORT]
        export_names = {e.name for e in exports}
        assert "Dog" in export_names
        assert "bark" in export_names

        # Field Definitions
        definitions = [
            s for s in result.symbols if s.symbol_type == SymbolType.DEFINITION
        ]
        assert any(d.name == "MAX_AGE" for d in definitions)

        # Method Calls
        calls = [s for s in result.symbols if s.symbol_type == SymbolType.CALL]
        call_names = {c.name for c in calls}
        assert "super" in call_names
        assert "println" in call_names
        assert "recordSound" in call_names


# -------------------------------------------------------------------------
# 5. Graceful Failure Tests
# -------------------------------------------------------------------------
class TestParserGracefulFailure:
    """Verifies that parsers handle syntax errors and edge cases without crashing."""

    def test_syntax_error_recovers_gracefully(self):
        parser = PythonParser()
        broken_code = """
def valid_one():
    return 1

def broken_func(
    x =
"""
        result = parser.parse(broken_code, "broken.py")
        # Tree-sitter notes syntax errors but does not crash
        assert result.has_errors is True
        # Still extracted the valid function!
        assert any(s.name == "valid_one" for s in result.symbols)

    def test_empty_source_code(self):
        for parser in [
            PythonParser(),
            JavaScriptParser(),
            TypeScriptParser(),
            JavaParser(),
        ]:
            res = parser.parse("", "empty_file")
            assert res.symbols == []
            assert res.has_errors is False

    def test_invalid_input_type(self):
        parser = PythonParser()
        res = parser.parse(12345, "invalid")  # type: ignore
        assert res.has_errors is True
        assert "Invalid code input type" in res.error_message

    def test_unknown_extension_lookup(self):
        p = get_parser_for_file("archive.zip")
        assert p is None
        res = parse_source_code("random content", "archive.zip")
        assert res.symbols == []
        assert "No parser available" in res.error_message


# -------------------------------------------------------------------------
# 6. Parser Registry & Extensibility Tests
# -------------------------------------------------------------------------
class TestParserRegistry:
    """Verifies registry lookup and runtime extensibility for new languages."""

    def test_default_parsers_registered(self):
        assert get_parser_for_language("python") is not None
        assert get_parser_for_language("typescript") is not None
        assert get_parser_for_language("javascript") is not None
        assert get_parser_for_language("java") is not None

        assert get_parser_for_extension(".py") is not None
        assert get_parser_for_extension(".ts") is not None
        assert get_parser_for_extension(".js") is not None
        assert get_parser_for_extension(".java") is not None

    def test_register_custom_language_parser(self):
        """Demonstrates adding an additional language parser abstraction."""

        class MockGoParser(BaseLanguageParser):
            @property
            def language_name(self) -> str:
                return "Go"

            @property
            def supported_extensions(self) -> set[str]:
                return {".go"}

            def get_tree_sitter_language(self):
                # Return python language as a mock stand-in
                return PythonParser().get_tree_sitter_language()

            def extract_symbols(self, root_node, code_bytes, file_path):
                return [
                    ParsedSymbol(
                        symbol_type=SymbolType.FUNCTION,
                        name="main",
                        qualified_name="main",
                        start_line=1,
                        end_line=3,
                        signature="func main()",
                    )
                ]

        registry = ParserRegistry()
        mock_go = MockGoParser()
        registry.register_parser(mock_go)

        assert "Go" in registry.supported_languages()
        assert registry.get_parser_for_extension(".go") is mock_go
        assert registry.get_parser_for_language("go") is mock_go

        res = registry.get_parser_for_file("main.go").parse("func main() {}")
        assert len(res.symbols) == 1
        assert res.symbols[0].name == "main"


# -------------------------------------------------------------------------
# 7. Database Persistence & Hierarchy Tests
# -------------------------------------------------------------------------
class TestSymbolDatabasePersistence:
    """Verifies persisting parsed symbols to SQLite DB with parent_symbol_id linking."""

    def test_persist_symbols_with_parent_hierarchy(
        self, db_session: Session, tmp_path: Path
    ):
        # 1. Create Repository and RepositoryFile
        repo = Repository(
            name="test/symbols-repo",
            github_url="https://github.com/test/symbols-repo",
            default_branch="main",
            status=RepositoryStatus.READY,
        )
        db_session.add(repo)
        db_session.commit()
        db_session.refresh(repo)

        file_rec = RepositoryFile(
            repository_id=repo.id,
            path="src/calc.py",
            filename="calc.py",
            extension=".py",
            language="Python",
            size_bytes=200,
        )
        db_session.add(file_rec)
        db_session.commit()
        db_session.refresh(file_rec)

        # 2. Write file on disk and parse
        py_file = tmp_path / "calc.py"
        py_file.write_text(
            """
class Calculator:
    def add(self, a, b):
        return a + b
"""
        )

        symbols = parse_and_store_file_symbols(
            db=db_session,
            repository_id=repo.id,
            file_record=file_rec,
            file_path=py_file,
        )

        assert len(symbols) >= 2
        class_sym = next(s for s in symbols if s.symbol_type == "class")
        method_sym = next(s for s in symbols if s.symbol_type == "method")

        assert class_sym.name == "Calculator"
        assert method_sym.name == "add"
        # Verify parent_symbol_id links method to class!
        assert method_sym.parent_symbol_id == class_sym.id
        assert method_sym.parent == class_sym
        assert method_sym in class_sym.children

        # Verify querying by indexed columns
        q_syms = (
            db_session.query(Symbol)
            .filter(
                Symbol.repository_id == repo.id,
                Symbol.symbol_type == "method",
            )
            .all()
        )
        assert len(q_syms) == 1
        assert q_syms[0].qualified_name == "Calculator.add"


# -------------------------------------------------------------------------
# 8. Symbols REST API Tests
# -------------------------------------------------------------------------
class TestSymbolsApi:
    """Verifies REST endpoints for querying symbols."""

    def test_get_repository_symbols_and_file_symbols(
        self, db_session: Session, override_get_db
    ):
        repo = Repository(
            name="pallets/flask",
            github_url="https://github.com/pallets/flask",
            default_branch="main",
            status=RepositoryStatus.READY,
        )
        db_session.add(repo)
        db_session.commit()
        db_session.refresh(repo)

        file_rec = RepositoryFile(
            repository_id=repo.id,
            path="flask/app.py",
            filename="app.py",
            extension=".py",
            language="Python",
            size_bytes=5000,
        )
        db_session.add(file_rec)
        db_session.commit()
        db_session.refresh(file_rec)

        sym1 = Symbol(
            repository_id=repo.id,
            file_id=file_rec.id,
            symbol_type="class",
            name="Flask",
            qualified_name="Flask",
            start_line=10,
            end_line=200,
            signature="class Flask(Scaffold):",
        )
        db_session.add(sym1)
        db_session.commit()
        db_session.refresh(sym1)

        sym2 = Symbol(
            repository_id=repo.id,
            file_id=file_rec.id,
            symbol_type="method",
            name="run",
            qualified_name="Flask.run",
            start_line=50,
            end_line=60,
            signature="def run(self):",
            parent_symbol_id=sym1.id,
        )
        db_session.add(sym2)
        db_session.commit()

        # Test GET /api/repositories/{id}/symbols
        res = client.get(f"/api/repositories/{repo.id}/symbols?page=1&page_size=10")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

        # Test filter by symbol_type
        res_filter = client.get(
            f"/api/repositories/{repo.id}/symbols?symbol_type=class"
        )
        assert res_filter.status_code == 200
        class_data = res_filter.json()
        assert class_data["total"] == 1
        assert class_data["items"][0]["name"] == "Flask"

        # Test GET /api/repositories/{id}/files/{file_id}/symbols
        res_file_syms = client.get(
            f"/api/repositories/{repo.id}/files/{file_rec.id}/symbols"
        )
        assert res_file_syms.status_code == 200
        file_sym_data = res_file_syms.json()
        assert len(file_sym_data) == 2

        # Test 404 for non-existent repo
        assert client.get("/api/repositories/999999/symbols").status_code == 404
