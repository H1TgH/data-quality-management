from fastapi import APIRouter, Depends

from api.data_source.decorators import handle_data_source_exceptions
from api.dependencies import get_current_user, get_run_service
from api.projects.decorators import handle_project_exceptions
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
