import logging
import os

from .base import BaseLanguageParser
from .languages.java import JavaParser
from .languages.javascript import JavaScriptParser
from .languages.python import PythonParser
from .languages.typescript import TypeScriptParser

logger = logging.getLogger(__name__)


class ParserRegistry:
    """
    Registry for source code language parsers.
    Manages lookup by file extension or language name and allows registering
    new language parsers dynamically.
    """

    def __init__(self) -> None:
        self._parsers_by_name: dict[str, BaseLanguageParser] = {}
        self._parsers_by_extension: dict[str, BaseLanguageParser] = {}
        self._register_default_parsers()

    def _register_default_parsers(self) -> None:
        """Register the 4 initial parsers: Python, JavaScript, TypeScript, Java."""
        default_parsers: list[BaseLanguageParser] = [
            PythonParser(),
            TypeScriptParser(),
            JavaScriptParser(),
            JavaParser(),
        ]
        for parser in default_parsers:
            self.register_parser(parser)

    def register_parser(self, parser: BaseLanguageParser) -> None:
        """
        Register a new language parser.
        Maps the parser by normalized language name and all its supported extensions.
        """
        norm_name = parser.language_name.lower()
        self._parsers_by_name[norm_name] = parser

        for ext in parser.supported_extensions:
            norm_ext = ext.lower()
            if not norm_ext.startswith("."):
                norm_ext = f".{norm_ext}"
            self._parsers_by_extension[norm_ext] = parser

        logger.debug(
            "Registered parser for language '%s' with extensions: %s",
            parser.language_name,
            parser.supported_extensions,
        )

    def get_parser_for_language(self, language: str) -> BaseLanguageParser | None:
        """Retrieve parser by language name (case-insensitive)."""
        if not language:
            return None
        return self._parsers_by_name.get(language.strip().lower())

    def get_parser_for_extension(self, extension: str) -> BaseLanguageParser | None:
        """Retrieve parser by file extension (e.g. '.py', '.ts')."""
        if not extension:
            return None
        norm_ext = extension.strip().lower()
        if not norm_ext.startswith("."):
            norm_ext = f".{norm_ext}"
        return self._parsers_by_extension.get(norm_ext)

    def get_parser_for_file(self, file_path: str) -> BaseLanguageParser | None:
        """Retrieve parser matching the extension of the given file path."""
        if not file_path:
            return None
        ext = os.path.splitext(file_path)[1].lower()
        return self.get_parser_for_extension(ext)

    def supported_languages(self) -> list[str]:
        """Return list of supported language names."""
        return [p.language_name for p in self._parsers_by_name.values()]

    def supported_extensions(self) -> list[str]:
        """Return list of supported file extensions."""
        return sorted(self._parsers_by_extension.keys())


# Global default registry instance
default_registry = ParserRegistry()


def get_parser_for_file(file_path: str) -> BaseLanguageParser | None:
    """Convenience function to get parser for a given file path."""
    return default_registry.get_parser_for_file(file_path)


def get_parser_for_language(language: str) -> BaseLanguageParser | None:
    """Convenience function to get parser for a language name."""
    return default_registry.get_parser_for_language(language)


def get_parser_for_extension(extension: str) -> BaseLanguageParser | None:
    """Convenience function to get parser for a file extension."""
    return default_registry.get_parser_for_extension(extension)
