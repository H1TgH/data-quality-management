from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from core.rules.enums import RuleActionEnum, RuleTypeEnum


class RuleCreationSchema(BaseModel):
    name: str
    rule_type: RuleTypeEnum
    target_columns: list[str]
    params: dict
    action: RuleActionEnum
    is_active: bool = True


class RuleResponseSchema(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    rule_type: RuleTypeEnum
    target_columns: list[str]
    params: dict
    action: RuleActionEnum
    is_active: bool
    created_at: datetime


class RulesListResponseSchema(BaseModel):
    items: list[RuleResponseSchema]
    total: int


class RuleIsActiveSchema(BaseModel):
    is_active: bool
