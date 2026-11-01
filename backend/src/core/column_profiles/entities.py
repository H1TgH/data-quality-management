from dataclasses import dataclass
from typing import Any


@dataclass
class ColumnMetadataDTO:
    name: str
    data_type: str
    ordinal_position: int


@dataclass
class ColumnProfileDTO:
    column_name: str
    data_type: str
    total_rows: int
    filled_rows: int
    completeness: float
    min_value: Any | None = None
    max_value: Any | None = None


@dataclass
class TableProfileDTO:
    table_name: str
    total_rows: int
    columns: list[ColumnProfileDTO]
