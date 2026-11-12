from core.data_sources.enums import DataSourceTypeEnum
from core.data_sources.exceptions import DataSourceConfigurationException, DataSourceNotFoundException
from core.data_sources.service import DataSourceService
from core.projects.entities import ProjectCreationDTO
from infrastructure.database.repositories.project import ProjectRepository


class ProjectService:
    def __init__(
        self,
        data_source_service: DataSourceService,
        project_repository: ProjectRepository,
    ) -> None:
        self.data_source_service = data_source_service
        self.project_repo = project_repository

    async def create_project(
        self,
        data: ProjectCreationDTO
    ) -> str:
        data_source_type = await self.data_source_service.get_data_source_type(data.data_source_id)
        if data_source_type is None:
            raise DataSourceNotFoundException(
                f"Источник данных с id: {data.data_source_id} не найден"
            )

        if data_source_type != DataSourceTypeEnum.DB:
            raise DataSourceConfigurationException(
                "Выбрать таблицу можно только для источника типа БД"
            )

        tables = await self.data_source_service.get_tables(data.data_source_id)
        table_full_name = f"{data.schema_name}.{data.table_name}"
        if table_full_name not in tables.tables_full_name:
            raise DataSourceConfigurationException(
                f"Таблица {table_full_name} не найдена в источнике данных"
            )

        project_name = data.name or table_full_name
        return await self.project_repo.create(
            data_source_id=data.data_source_id,
            name=project_name,
            schema_name=data.schema_name,
            table_name=data.table_name,
        )
