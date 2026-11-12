from pydantic import BaseModel


class ProjectCreationSchema(BaseModel):
    data_source_id: str
    schema_name: str
    table_name: str
    name: str | None = None


class ProjectCreationResponseSchema(BaseModel):
    project_id: str
