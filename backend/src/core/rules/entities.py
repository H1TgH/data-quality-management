from dataclasses import dataclass
from datetime import datetime

from core.rules.enums import RuleActionEnum, RuleTypeEnum


@dataclass
class RuleCreationDTO:
    project_id: str
    name: str
    rule_type: RuleTypeEnum
    target_columns: list[str]
    params: dict
    action: RuleActionEnum
    is_active: bool


@dataclass
class RuleReadDTO:
    id: str
    project_id: str
    name: str
    rule_type: RuleTypeEnum
    target_columns: list[str]
    params: dict
    action: RuleActionEnum
    is_active: bool
    created_at: datetime


@dataclass
class RulesListResponseDTO:
    items: list[RuleReadDTO]
    total: int
