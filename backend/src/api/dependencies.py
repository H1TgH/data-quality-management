from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.column_profiles.service import ColumnProfileService
from core.data_sources.entities import DataSourceCredsDTO
from core.data_sources.file_service import FileDataSourceService
from core.data_sources.service import DataSourceService
from core.projects.service import ProjectService
from core.rules.service import RuleService
from core.runs.service import RunService
from infrastructure.database.database import Session
from infrastructure.database.repositories.data_source import DataSourceRepository
from infrastructure.database.repositories.cleaned_rows import CleanedRowsRepository
from infrastructure.database.repositories.error_log import ErrorLogRepository
from infrastructure.database.repositories.project import ProjectRepository
from infrastructure.database.repositories.rule import RuleRepository
from infrastructure.database.repositories.run import RunRepository
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


def get_run_repository(
    session: AsyncSession = Depends(get_session)
) -> RunRepository:
    return RunRepository(session)


def get_error_log_repository(
    session: AsyncSession = Depends(get_session)
) -> ErrorLogRepository:
    return ErrorLogRepository(session)


def get_cleaned_rows_repository(
    session: AsyncSession = Depends(get_session)
) -> CleanedRowsRepository:
    return CleanedRowsRepository(session)


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
    data_source_service: DataSourceService = Depends(get_data_source_service)
) -> ColumnProfileService:
    return ColumnProfileService(
        data_source_service=data_source_service,
        external_client=PostgresClient(),
        staging_credentials=DataSourceCredsDTO(
            host=settings.db.host,
            port=settings.db.port,
            db_name=settings.db.db,
            user=settings.db.user,
            password=settings.db.password.get_secret_value(),
        ),
    )


def get_file_data_source_service(
    data_source_service: DataSourceService = Depends(get_data_source_service),
    project_service: ProjectService = Depends(get_project_service),
) -> FileDataSourceService:
    return FileDataSourceService(
        data_source_service=data_source_service,
        project_service=project_service,
        staging_loader=StagingLoader(settings.db.app_db_connection_params),
    )


def get_rule_service(
    rule_repository: RuleRepository = Depends(get_rule_repository),
    project_service: ProjectService = Depends(get_project_service),
) -> RuleService:
    return RuleService(
        rule_repository=rule_repository,
        project_service=project_service,
    )


def get_run_service(
    project_service: ProjectService = Depends(get_project_service),
    rule_service: RuleService = Depends(get_rule_service),
    data_source_service: DataSourceService = Depends(get_data_source_service),
    run_repository: RunRepository = Depends(get_run_repository),
    error_log_repository: ErrorLogRepository = Depends(get_error_log_repository),
    cleaned_rows_repository: CleanedRowsRepository = Depends(get_cleaned_rows_repository),
) -> RunService:
    return RunService(
        project_service=project_service,
        rule_service=rule_service,
        data_source_service=data_source_service,
        run_repository=run_repository,
        error_log_repository=error_log_repository,
        cleaned_rows_repository=cleaned_rows_repository,
        postgres_client=PostgresClient(),
        staging_credentials=DataSourceCredsDTO(
            host=settings.db.host,
            port=settings.db.port,
            db_name=settings.db.db,
            user=settings.db.user,
            password=settings.db.password.get_secret_value(),
        ),
    )
