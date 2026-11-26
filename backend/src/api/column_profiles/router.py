from fastapi import APIRouter, Depends

from api.column_profiles.schemas import TableProfileSchema
from api.data_source.decorators import handle_data_source_exceptions
from api.dependencies import get_column_profile_service, get_current_user
from core.column_profiles.service import ColumnProfileService
from core.users.entities import CurrentUserDTO


router = APIRouter(
    prefix="/column-profiles",
    tags=["column-profiles"],
)


@router.get(
    "/{source_id}/tables/{schema}/{table_name}",
    response_model=TableProfileSchema,
)
@handle_data_source_exceptions
async def profile_table(
    source_id: str,
    schema: str,
    table_name: str,
    current_user: CurrentUserDTO = Depends(get_current_user),
    service: ColumnProfileService = Depends(get_column_profile_service),
) -> TableProfileSchema:

    return await service.profile_table(
        source_id=source_id,
        schema=schema,
        table_name=table_name,
        user_id=current_user.id,
    )


@router.get(
    "/{source_id}/file",
    response_model=TableProfileSchema,
)
@handle_data_source_exceptions
async def profile_file(
    source_id: str,
    current_user: CurrentUserDTO = Depends(get_current_user),
    service: ColumnProfileService = Depends(get_column_profile_service),
) -> TableProfileSchema:
    return await service.profile_file(source_id, current_user.id)
