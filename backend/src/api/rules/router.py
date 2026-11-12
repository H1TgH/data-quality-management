from fastapi import APIRouter, Depends, Response, status

from api.dependencies import get_rule_service
from api.rules.decorators import handle_rule_exceptions
from api.rules.schemas import (
    RuleCreationSchema,
    RuleIsActiveSchema,
    RuleResponseSchema,
    RulesListResponseSchema,
)
from core.rules.entities import RuleCreationDTO
from core.rules.service import RuleService


router = APIRouter(
    prefix="/{project_id}/rules",
    tags=["rules"]
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED
)
@handle_rule_exceptions
async def create_rule(
    project_id: str,
    data: RuleCreationSchema,
    service: RuleService = Depends(get_rule_service)
):
    rule_id = await service.create_rule(
        RuleCreationDTO(
            project_id=project_id,
            **data.model_dump()
        )
    )

    return {
        "rule_id": rule_id
    }


@router.get(
    "/",
    response_model=RulesListResponseSchema,
)
@handle_rule_exceptions
async def get_rules(
    project_id: str,
    service: RuleService = Depends(get_rule_service),
):
    return await service.get_rules_list(project_id)


@router.get(
    "/{rule_id}",
    response_model=RuleResponseSchema,
)
@handle_rule_exceptions
async def get_rule(
    project_id: str,
    rule_id: str,
    service: RuleService = Depends(get_rule_service),
):
    rule = await service.get_rule(project_id, rule_id)

    return rule


@router.put(
    "/{rule_id}",
    response_model=RuleResponseSchema,
)
@handle_rule_exceptions
async def update_rule(
    project_id: str,
    rule_id: str,
    data: RuleCreationSchema,
    service: RuleService = Depends(get_rule_service),
):
    return await service.update_rule(
        project_id=project_id,
        rule_id=rule_id,
        rule_data=RuleCreationDTO(
            project_id=project_id,
            **data.model_dump()
        ),
    )


@router.patch(
    "/{rule_id}/active",
    response_model=RuleResponseSchema,
)
@handle_rule_exceptions
async def set_rule_is_active(
    project_id: str,
    rule_id: str,
    data: RuleIsActiveSchema,
    service: RuleService = Depends(get_rule_service),
):
    return await service.set_rule_is_active(
        project_id=project_id,
        rule_id=rule_id,
        is_active=data.is_active,
    )


@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@handle_rule_exceptions
async def delete_rule(
    project_id: str,
    rule_id: str,
    service: RuleService = Depends(get_rule_service),
):
    await service.delete_rule(project_id, rule_id)
