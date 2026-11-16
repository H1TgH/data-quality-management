from fastapi import APIRouter, Depends

from api.dependencies import get_run_service
from core.runs.service import RunService


router = APIRouter(
    prefix="/run",
    tags=["runs"]
)


@router.post(
    "/{project_id}",
)
async def run_check(
    project_id: str,
    service: RunService = Depends(get_run_service)
):
    return await service.run_check(project_id)
