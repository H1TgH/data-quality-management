from fastapi import APIRouter, Depends

from api.column_profiles.schemas import TableProfileSchema
from api.dependencies import get_column_profile_service
from core.column_profiles.service import ColumnProfileService


router = APIRouter(
    prefix="/column-profiles",
    tags=["Column Profiles"],
)


@router.get(
    "/{source_id}/tables/{schema}/{table_name}",
    response_model=TableProfileSchema,
)
async def profile_table(
    source_id: str,
    schema: str,
    table_name: str,
    service: ColumnProfileService = Depends(get_column_profile_service),
) -> TableProfileSchema:

    return await service.profile_table(
        source_id=source_id,
        schema=schema,
        table_name=table_name,
    )


@router.get(
    "/{source_id}/file",
    response_model=TableProfileSchema,
)
async def profile_file(
    source_id: str,
    service: ColumnProfileService = Depends(get_column_profile_service),
) -> TableProfileSchema:
    return await service.profile_file(source_id)
