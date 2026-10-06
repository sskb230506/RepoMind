from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SymbolResponse(BaseModel):
    """Schema representing a parsed source code symbol."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique symbol ID")
    repository_id: int = Field(..., description="ID of associated repository")
    file_id: int = Field(..., description="ID of associated repository file")
    symbol_type: str = Field(
        ...,
        description=(
            "Type of symbol (function, method, class, import, "
            "export, call, inheritance, definition)"
        ),
    )
    name: str = Field(..., description="Symbol identifier name")
    qualified_name: str = Field(..., description="Full hierarchical qualified name")
    start_line: int = Field(..., description="Starting line in source file (1-based)")
    end_line: int = Field(..., description="Ending line in source file (1-based)")
    signature: str | None = Field(
        None, description="Signature line or declaration snippet"
    )
    parent_symbol_id: int | None = Field(
        None, description="ID of parent symbol (e.g. enclosing class or function)"
    )
    created_at: datetime = Field(..., description="Creation timestamp")


class PaginatedSymbolsResponse(BaseModel):
    """Paginated list of repository symbols."""

    total: int = Field(..., description="Total count of symbols matching criteria")
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total available pages")
    items: list[SymbolResponse] = Field(..., description="List of symbols on this page")
