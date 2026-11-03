from dataclasses import asdict

from fastapi import APIRouter, Depends, File, UploadFile, status

from api.data_source.decorators import handle_data_source_exceptions
from api.data_source.schemas import DataSourceCreationSchema, DataSourceTablesResponseSchema, FileUploadResponseSchema
from api.dependencies import get_data_source_service, get_file_data_source_service
from core.data_sources.entities import DataSourceCreationDTO
from core.data_sources.enums import DataSourceTypeEnum
from core.data_sources.file_service import FileDataSourceService
from core.data_sources.service import DataSourceService


router = APIRouter(
    prefix="/data-sources",
    tags=["data-sources"]
)


async def _iter_chunks(file: UploadFile, size: int = 1024 * 1024):
    while chunk := await file.read(size):
        yield chunk


@router.post(
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


@router.get(
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


@router.post(
    "/file",
    status_code=status.HTTP_201_CREATED,
    response_model=FileUploadResponseSchema,
)
@handle_data_source_exceptions
async def upload_file(
    file: UploadFile = File(...),
    service: FileDataSourceService = Depends(get_file_data_source_service),
):
    result = await service.upload(
        filename=file.filename or "",
        chunks=_iter_chunks(file),
    )
    return FileUploadResponseSchema(**asdict(result))
