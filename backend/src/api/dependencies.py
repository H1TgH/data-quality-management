from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.column_profiles.service import ColumnProfileService
from core.data_sources.file_service import FileDataSourceService
from core.data_sources.service import DataSourceService
from core.projects.service import ProjectService
from core.rules.service import RuleService
from infrastructure.database.database import Session
from infrastructure.database.repositories.data_source import DataSourceRepository
from infrastructure.database.repositories.project import ProjectRepository
from infrastructure.database.repositories.rule import RuleRepository
from infrastructure.database.staging_loader import StagingLoader
from infrastructure.external_databases.postgres_client import PostgresClient
from settings import settings


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


def get_rule_repository(
    session: AsyncSession = Depends(get_session)
) -> RuleRepository:
    return RuleRepository(session)


def get_data_source_service(
    data_source_repository: DataSourceRepository = Depends(get_data_source_repository)
) -> DataSourceService:
    return DataSourceService(data_source_repository)


def get_project_service(
    data_source_service: DataSourceService = Depends(get_data_source_service),
    session: AsyncSession = Depends(get_session),
) -> ProjectService:
    return ProjectService(
        data_source_service=data_source_service,
        project_repository=ProjectRepository(session),
    )


def get_column_profile_service(
    data_source_repository: DataSourceRepository = Depends(get_data_source_repository)
) -> ColumnProfileService:
    return ColumnProfileService(
        data_source_repository=data_source_repository,
        external_client=PostgresClient(),
    )


def get_file_data_source_service(
    session: AsyncSession = Depends(get_session)
) -> FileDataSourceService:
    return FileDataSourceService(
        data_source_repository=DataSourceRepository(session),
        project_repository=ProjectRepository(session),
        staging_loader=StagingLoader(settings.db.app_db_connection_params),
    )


def get_rule_service(
    rule_repository: RuleRepository = Depends(get_rule_repository)
) -> RuleService:
    return RuleService(
        rule_repository=rule_repository
    )
