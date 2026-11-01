from typing import Any

from pydantic import BaseModel


class ColumnProfileSchema(BaseModel):
    column_name: str
    data_type: str
    total_rows: int
    filled_rows: int
    completeness: float
    min_value: Any | None = None
    max_value: Any | None = None


class TableProfileSchema(BaseModel):
    table_name: str
    total_rows: int
    columns: list[ColumnProfileSchema]
