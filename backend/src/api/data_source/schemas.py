from pydantic import BaseModel, Field


class DataSourceCreationSchema(BaseModel):
    host: str
    port: int
    db_name: str
    username: str
    password: str


class DataSourceTablesResponseSchema(BaseModel):
    tables_full_name: list[str] = Field(serialization_alias="tables")
    total: int
