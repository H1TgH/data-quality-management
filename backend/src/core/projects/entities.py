from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProjectCreationDTO:
    user_id: str
    data_source_id: str
    schema_name: str
    table_name: str
    name: str | None = None


@dataclass
class ProjectReadDTO:
    id: str
    user_id: str
    data_source_id: str
    name: str
    schema_name: str | None
    table_name: str


@dataclass
class ProjectListItemDTO:
    id: str
    data_source_id: str
    name: str
    schema_name: str | None
    table_name: str
    source_name: str
    quality_score: float | None
    last_run_at: datetime | None
    last_run_status: str | None
