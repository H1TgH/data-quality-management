from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from core.runs.enums import RunStatusEnum, RunTriggerEnum


class RunResponseSchema(BaseModel):
    id: UUID
    project_id: UUID
    trigger: RunTriggerEnum
    status: RunStatusEnum
    started_at: datetime
    finished_at: datetime | None
    rows_total: int | None
    rows_removed: int | None
    errors_count: int | None
    quality_score: float | None


class ErrorGroupSchema(BaseModel):
    rule_id: UUID | None
    rule_name: str | None
    rule_type: str
    action: str | None
    field_name: str
    rows_count: int
    expected_condition: dict[str, Any] | None


class ErrorRowSchema(BaseModel):
    id: UUID
    row_data: dict[str, Any]
    status: str


class ErrorRowsSchema(BaseModel):
    items: list[ErrorRowSchema]
    total: int


class CleanZonePublicationSchema(BaseModel):
    publication_id: UUID
    view_name: str
    quality_score: float
