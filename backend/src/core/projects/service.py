from core.data_sources.enums import DataSourceTypeEnum
from core.data_sources.exceptions import DataSourceConfigurationException, DataSourceNotFoundException
from core.data_sources.service import DataSourceService
from core.projects.entities import (
    ProjectCreationDTO,
    ProjectListItemDTO,
    ProjectReadDTO,
    ProjectsListDTO,
    ProjectsSummaryDTO,
)
from core.projects.exceptions import ProjectNotFoundException
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
        data_source_type = await self.data_source_service.get_data_source_type(
            data.data_source_id,
            data.user_id,
        )
        if data_source_type is None:
            raise DataSourceNotFoundException(
                f"Источник данных с id: {data.data_source_id} не найден"
            )

        if data_source_type != DataSourceTypeEnum.DB:
            raise DataSourceConfigurationException(
                "Выбрать таблицу можно только для источника типа БД"
            )

        tables = await self.data_source_service.get_tables(data.data_source_id, data.user_id)
        table_full_name = f"{data.schema_name}.{data.table_name}"
        if table_full_name not in tables.tables_full_name:
            raise DataSourceConfigurationException(
                f"Таблица {table_full_name} не найдена в источнике данных"
            )

        if not data.name:
            data.name = table_full_name
        return await self.project_repo.create(data)

    async def create_file_project(
        self,
        data_source_id: str,
        user_id: str,
        name: str,
        table_name: str,
    ) -> str:
        data_source_type = await self.data_source_service.get_data_source_type(data_source_id, user_id)
        if data_source_type is None:
            raise DataSourceNotFoundException(
                f"Источник данных с id: {data_source_id} не найден"
            )

        if data_source_type != DataSourceTypeEnum.FILE:
            raise DataSourceConfigurationException(
                "Файловый проект можно создать только для источника типа файл"
            )

        return await self.project_repo.create(ProjectCreationDTO(
            user_id=user_id,
            data_source_id=data_source_id,
            name=name,
            schema_name="staging",
            table_name=table_name,
        ))

    async def get_project(self, project_id: str, user_id: str) -> ProjectReadDTO:
        project = await self.project_repo.get_by_id(project_id, user_id)
        if project is None:
            raise ProjectNotFoundException(f"Проект с id: {project_id} не найден")

        return ProjectReadDTO(
            id=str(project.id),
            user_id=str(project.user_id),
            data_source_id=str(project.data_source_id),
            name=project.name,
            schema_name=project.schema_name,
            table_name=project.table_name,
        )

    async def get_projects_list(self, user_id: str) -> ProjectsListDTO:
        projects = await self.project_repo.get_projects_list(user_id)

        items = [
            ProjectListItemDTO(
                id=str(project.id),
                data_source_id=str(project.data_source_id),
                name=project.name,
                schema_name=project.schema_name,
                table_name=project.table_name,
                source_name=project.source_name,
                quality_score=(
                    float(project.quality_score)
                    if project.quality_score is not None else None
                ),
                last_run_at=project.last_run_at,
                last_run_status=(
                    str(project.last_run_status)
                    if project.last_run_status is not None else None
                ),
                errors_count=project.errors_count,
            )
            for project in projects
        ]

        projects_with_score = [
            project.quality_score
            for project in items
            if project.quality_score is not None
        ]

        return ProjectsListDTO(
            summary=ProjectsSummaryDTO(
                active_projects=len(items),
                average_quality_score=(
                    int(sum(projects_with_score) / len(projects_with_score))
                    if projects_with_score else None
                ),
                projects_requiring_attention=sum(
                    1 for project in items
                    if project.errors_count is not None and project.errors_count > 0
                ),
            ),
            items=items,
        )
