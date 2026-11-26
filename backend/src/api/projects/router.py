from fastapi import APIRouter, Depends, status

from api.data_source.decorators import handle_data_source_exceptions
from core.users.entities import CurrentUserDTO
from api.dependencies import get_project_service
from api.projects.schemas import (
    ProjectCreationResponseSchema,
    ProjectCreationSchema,
    ProjectListItemSchema,
)
from core.projects.entities import ProjectCreationDTO
from core.projects.service import ProjectService
from api.dependencies import get_current_user


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
    current_user: CurrentUserDTO = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
):
    project_id = await service.create_project(
        ProjectCreationDTO(
            **data.model_dump(),
            user_id=current_user.id
        )
    )

    return {
        "project_id": project_id
    }


@router.get(
    "/",
    response_model=list[ProjectListItemSchema],
)
async def get_projects(
    service: ProjectService = Depends(get_project_service),
):
    return await service.get_projects_list()
