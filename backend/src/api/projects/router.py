from fastapi import APIRouter, Depends, status

from api.data_source.decorators import handle_data_source_exceptions
from api.dependencies import get_project_service
from api.projects.schemas import ProjectCreationResponseSchema, ProjectCreationSchema
from core.projects.entities import ProjectCreationDTO
from core.projects.service import ProjectService


router = APIRouter(
    prefix="/projects",
    tags=["projects"]
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=ProjectCreationResponseSchema,
)
@handle_data_source_exceptions
async def create_project(
    data: ProjectCreationSchema,
    service: ProjectService = Depends(get_project_service),
):
    project_id = await service.create_project(
        ProjectCreationDTO(**data.model_dump())
    )

    return {
        "project_id": project_id
    }
