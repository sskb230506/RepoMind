import logging
import os
from pathlib import Path

from sqlalchemy.orm import Session

try:
    from backend.app.models.repository_file import RepositoryFile
    from backend.app.models.symbol import Symbol
    from backend.app.parser import (
        BaseLanguageParser,
        ParsedSymbol,
        ParseResult,
        get_parser_for_file,
    )
except ModuleNotFoundError:
    from app.models.repository_file import RepositoryFile
    from app.models.symbol import Symbol
    from app.parser import (
        BaseLanguageParser,
        ParsedSymbol,
        ParseResult,
        get_parser_for_file,
    )

logger = logging.getLogger(__name__)


def parse_source_code(
    code: str | bytes,
    file_path: str = "",
    parser: BaseLanguageParser | None = None,
) -> ParseResult:
    """
    Parse source code using a resolved or provided language parser.
    Fails gracefully if unsupported or malformed.
    """
    if parser is None:
        parser = get_parser_for_file(file_path)

    if parser is None:
        ext = os.path.splitext(file_path)[1]
        return ParseResult(
            language="Unknown",
            symbols=[],
            has_errors=False,
            error_message=f"No parser available for extension '{ext}'",
        )

    return parser.parse(code, file_path=file_path)


def persist_parsed_symbols(
    db: Session,
    repository_id: int,
    file_id: int,
    parsed_symbols: list[ParsedSymbol],
) -> list[Symbol]:
    """
    Persist extracted symbols to database with parent_symbol_id hierarchy resolution.
    Clears any prior symbols for the file to ensure idempotency.
    """
    # 1. Clear existing symbols for this file
    db.query(Symbol).filter(
        Symbol.repository_id == repository_id,
        Symbol.file_id == file_id,
    ).delete(synchronize_session=False)

    if not parsed_symbols:
        db.commit()
        return []

    # 2. Instantiate Symbol model records
    db_symbols: list[Symbol] = []
    for s in parsed_symbols:
        sym_type_val = (
            s.symbol_type.value
            if hasattr(s.symbol_type, "value")
            else str(s.symbol_type)
        )
        db_symbols.append(
            Symbol(
                repository_id=repository_id,
                file_id=file_id,
                symbol_type=sym_type_val,
                name=s.name,
                qualified_name=s.qualified_name,
                start_line=s.start_line,
                end_line=s.end_line,
                signature=s.signature,
            )
        )

    db.add_all(db_symbols)
    db.flush()  # Flush to generate primary key IDs

    # 3. Resolve parent_symbol_id using parent_index pointers
    for i, s in enumerate(parsed_symbols):
        if s.parent_index is not None and 0 <= s.parent_index < len(db_symbols):
            parent_sym = db_symbols[s.parent_index]
            db_symbols[i].parent_symbol_id = parent_sym.id

    db.commit()
    for sym in db_symbols:
        db.refresh(sym)

    return db_symbols


def parse_and_store_file_symbols(
    db: Session,
    repository_id: int,
    file_record: RepositoryFile,
    file_path: Path,
) -> list[Symbol]:
    """
    Read source file from disk, parse AST symbols, and save them in the database.
    Fails gracefully on unreadable files, encoding errors, or syntax errors.
    """
    parser = get_parser_for_file(file_record.path)
    if not parser:
        return []

    try:
        content = file_path.read_bytes()
    except OSError as e:
        logger.warning("Failed to read file %s for symbol parsing: %s", file_path, e)
        return []

    parse_result = parser.parse(content, file_path=file_record.path)
    if not parse_result.symbols:
        return []

    return persist_parsed_symbols(
        db=db,
        repository_id=repository_id,
        file_id=file_record.id,
        parsed_symbols=parse_result.symbols,
    )


def parse_repository_symbols(
    db: Session,
    repository_id: int,
    repo_dir: Path,
) -> int:
    """
    Parse symbols for all supported, non-binary source files in a repository.
    Returns total number of symbols stored.
    """
    files = (
        db.query(RepositoryFile)
        .filter(
            RepositoryFile.repository_id == repository_id,
            RepositoryFile.is_binary.is_(False),
        )
        .all()
    )

    total_symbols = 0
    for f in files:
        parser = get_parser_for_file(f.path)
        if not parser:
            continue

        full_path = repo_dir / f.path
        if not full_path.exists():
            continue

        created = parse_and_store_file_symbols(
            db=db,
            repository_id=repository_id,
            file_record=f,
            file_path=full_path,
        )
        total_symbols += len(created)

    logger.info(
        "Extracted and stored %d symbols for repository %d",
        total_symbols,
        repository_id,
    )
    return total_symbols
