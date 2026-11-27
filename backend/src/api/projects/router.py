from fastapi import APIRouter, Depends, status

from api.data_source.decorators import handle_data_source_exceptions
from api.dependencies import get_current_user, get_project_service
from api.projects.schemas import (
    ProjectCreationResponseSchema,
    ProjectCreationSchema,
    ProjectsListSchema,
)
from core.projects.entities import ProjectCreationDTO
from core.projects.service import ProjectService
from core.users.entities import CurrentUserDTO


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
    response_model=ProjectsListSchema,
)
async def get_projects(
    current_user: CurrentUserDTO = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
):
    return await service.get_projects_list(current_user.id)
