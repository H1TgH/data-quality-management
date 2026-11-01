from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.column_profiles.service import ColumnProfileService
from core.data_sources.service import DataSourceService
from infrastructure.database.database import Session
from infrastructure.database.repositories.data_source import DataSourceRepository
from infrastructure.external_databases.postgres_client import PostgresClient


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with Session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_data_source_repository(
    session: AsyncSession = Depends(get_session)
) -> DataSourceRepository:
    return DataSourceRepository(session)


def get_data_source_service(
    data_source_repository: DataSourceRepository = Depends(get_data_source_repository)
) -> DataSourceService:
    return DataSourceService(data_source_repository)


def get_column_profile_service(
    data_source_repository: DataSourceRepository = Depends(get_data_source_repository)
) -> ColumnProfileService:
    return ColumnProfileService(
        data_source_repository=data_source_repository,
        external_client=PostgresClient(),
    )
