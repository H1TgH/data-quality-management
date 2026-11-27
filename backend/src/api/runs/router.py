import csv
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from api.data_source.decorators import handle_data_source_exceptions
from api.dependencies import get_current_user, get_run_service
from api.projects.decorators import handle_project_exceptions
from api.runs.schemas import (
    CleanZonePublicationSchema,
    ErrorGroupSchema,
    ErrorRowsSchema,
    QualityTrendPointSchema,
    RunResponseSchema,
)
from core.runs.exceptions import RunPublicationException
from core.runs.service import RunService
from core.users.entities import CurrentUserDTO


router = APIRouter(
    prefix="/run",
    tags=["runs"]
)


@router.post(
    "/{project_id}",
)
@handle_data_source_exceptions
@handle_project_exceptions
async def run_check(
    project_id: str,
    current_user: CurrentUserDTO = Depends(get_current_user),
    service: RunService = Depends(get_run_service)
):
    return await service.run_check(project_id, current_user.id)


@router.get(
    "/{project_id}",
    response_model=list[RunResponseSchema]
)
@handle_project_exceptions
async def get_runs(
    project_id: str,
    current_user: CurrentUserDTO = Depends(get_current_user),
    service: RunService = Depends(get_run_service),
):
    return await service.get_runs(project_id, current_user.id)


@router.get(
    "/{project_id}/analytics",
    response_model=list[QualityTrendPointSchema],
)
@handle_project_exceptions
async def get_quality_trend(
    project_id: str,
    period: str = Query(default="week", pattern="^(week|month)$"),
    current_user: CurrentUserDTO = Depends(get_current_user),
    service: RunService = Depends(get_run_service),
):
    return await service.get_quality_trend(project_id, current_user.id, period)


@router.get(
    "/{project_id}/{run_id}",
    response_model=RunResponseSchema
)
@handle_project_exceptions
async def get_run(
    project_id: str,
    run_id: str,
    current_user: CurrentUserDTO = Depends(get_current_user),
    service: RunService = Depends(get_run_service),
):
    run = await service.get_run(project_id, run_id, current_user.id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запуск не найден")
    return run


@router.get(
    "/{project_id}/{run_id}/errors",
    response_model=list[ErrorGroupSchema]
)
@handle_project_exceptions
async def get_error_groups(
    project_id: str,
    run_id: str,
    current_user: CurrentUserDTO = Depends(get_current_user),
    service: RunService = Depends(get_run_service),
):
    groups = await service.get_error_groups(project_id, run_id, current_user.id)
    if groups is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запуск не найден")
    return groups


@router.get(
    "/{project_id}/{run_id}/errors.csv"
)
@handle_project_exceptions
async def export_errors_csv(
    project_id: str,
    run_id: str,
    current_user: CurrentUserDTO = Depends(get_current_user),
    service: RunService = Depends(get_run_service),
):
    rows = await service.get_error_export_rows(project_id, run_id, current_user.id)
    if rows is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запуск не найден")

    columns = []
    for row in rows:
        for column in row.row_data:
            if column not in columns:
                columns.append(column)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["rule_name", "rule_type", "target_columns", *columns])
    for row in rows:
        writer.writerow([
            row.rule_name or "",
            row.rule_type,
            ", ".join(row.target_columns),
            *[row.row_data.get(column) for column in columns],
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="run-{run_id}-errors.csv"'},
    )


@router.get(
    "/{project_id}/{run_id}/errors/{rule_id}/{field_name}",
    response_model=ErrorRowsSchema,
)
@handle_project_exceptions
async def get_error_group_rows(
    project_id: str,
    run_id: str,
    rule_id: str,
    field_name: str,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    current_user: CurrentUserDTO = Depends(get_current_user),
    service: RunService = Depends(get_run_service),
):
    result = await service.get_error_group_rows(
        project_id, run_id, rule_id, field_name, current_user.id, offset, limit
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запуск не найден")
    return result


@router.get(
    "/{project_id}/{run_id}/errors/{rule_id}/{field_name}/sql"
)
@handle_project_exceptions
async def get_error_group_sql(
    project_id: str,
    run_id: str,
    rule_id: str,
    field_name: str,
    current_user: CurrentUserDTO = Depends(get_current_user),
    service: RunService = Depends(get_run_service),
):
    result = await service.get_error_group_sql(
        project_id, run_id, rule_id, field_name, current_user.id
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запуск не найден")
    return {"queries": result}


@router.patch(
    "/{project_id}/{run_id}/errors/{error_id}/valid"
)
@handle_project_exceptions
async def mark_error_row_valid(
    project_id: str,
    run_id: str,
    error_id: str,
    current_user: CurrentUserDTO = Depends(get_current_user),
    service: RunService = Depends(get_run_service),
):
    updated = await service.mark_error_row_valid(
        project_id, run_id, error_id, current_user.id
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ошибка не найдена")
    return {"msg": "Строка помечена как валидная"}


@router.post(
    "/{project_id}/{run_id}/publish",
    response_model=CleanZonePublicationSchema,
)
@handle_data_source_exceptions
@handle_project_exceptions
async def publish_to_clean_zone(
    project_id: str,
    run_id: str,
    current_user: CurrentUserDTO = Depends(get_current_user),
    service: RunService = Depends(get_run_service),
):
    try:
        return await service.publish_to_clean_zone(
            project_id, run_id, current_user.id
        )
    except RunPublicationException as exc:
        code = status.HTTP_404_NOT_FOUND if str(exc) == "Запуск не найден" else status.HTTP_409_CONFLICT
        raise HTTPException(status_code=code, detail=str(exc)) from exc
