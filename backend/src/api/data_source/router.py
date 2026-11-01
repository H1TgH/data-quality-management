from fastapi import APIRouter, Depends, status

from api.data_source.decorators import handle_data_source_exceptions
from api.data_source.schemas import DataSourceCreationSchema, DataSourceTablesResponseSchema
from api.dependencies import get_data_source_service
from core.data_sources.entities import DataSourceCreationDTO
from core.data_sources.enums import DataSourceTypeEnum
from core.data_sources.service import DataSourceService


data_source_router = APIRouter(
    prefix="/data-sources",
    tags=["data-sources"]
)


@data_source_router.post(
    "/db",
    status_code=status.HTTP_201_CREATED,
)
@handle_data_source_exceptions
async def create_data_sources(
    data: DataSourceCreationSchema,
    service: DataSourceService = Depends(get_data_source_service)
):
    source_id = await service.create(
        DataSourceCreationDTO(
            type=DataSourceTypeEnum.DB,
            **data.model_dump()
        )
    )

    return {
        "source_id": source_id
    }


@data_source_router.get(
    "/{source_id}/tables",
    status_code=status.HTTP_200_OK,
    response_model=DataSourceTablesResponseSchema
)
@handle_data_source_exceptions
async def get_tables(
    source_id: str,
    service: DataSourceService = Depends(get_data_source_service)
):
    return await service.get_tables(source_id)
