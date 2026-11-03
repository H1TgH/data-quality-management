from dataclasses import dataclass

from core.data_sources.enums import DataSourceTypeEnum


@dataclass
class DataSourceCreationDTO:
    type: DataSourceTypeEnum
    host: str
    port: int
    db_name: str
    username: str
    password: str


@dataclass
class DataSourceTablesDTO:
    table_name: str
    table_schema: str | None = None

    @property
    def table_full_name(self) -> str:
        if self.table_schema:
            return f"{self.table_schema}.{self.table_name}"
        return self.table_name


@dataclass
class DataSourceTablesResponseDTO:
    tables_full_name: list[str]
    total: int


@dataclass
class DataSourceCredsDTO:
    host: str
    port: int
    db_name: str
    user: str
    password: str


@dataclass
class FileSourceDTO:
    source_id: str
    file_name: str
    file_size_bytes: int
    row_count: int
    columns_count: int
