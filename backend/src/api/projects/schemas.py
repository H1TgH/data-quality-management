from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from core.runs.enums import RunStatusEnum


class ProjectCreationSchema(BaseModel):
    data_source_id: str
    schema_name: str
    table_name: str
    name: str | None = None


class ProjectCreationResponseSchema(BaseModel):
    project_id: str


class ProjectListItemSchema(BaseModel):
    id: UUID
    data_source_id: UUID
    name: str
    schema_name: str | None
    table_name: str
    source_name: str
    quality_score: float | None
    last_run_at: datetime | None
    last_run_status: RunStatusEnum | None
    errors_count: int | None


class ProjectsSummarySchema(BaseModel):
    active_projects: int
    average_quality_score: float | None
    projects_requiring_attention: int


class ProjectsListSchema(BaseModel):
    summary: ProjectsSummarySchema
    items: list[ProjectListItemSchema]
