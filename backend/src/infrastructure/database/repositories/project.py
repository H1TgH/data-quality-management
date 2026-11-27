from uuid import UUID, uuid4

from sqlalchemy import Row, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.projects.entities import ProjectCreationDTO


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        data: ProjectCreationDTO
    ) -> str:
        project_id = uuid4()
        await self.session.execute(
            text("""
                INSERT INTO projects (id, user_id, name, data_source_id, schema_name, table_name)
                VALUES (:id, :user_id, :name, :data_source_id, :schema_name, :table_name)
            """),
            {
                "id": project_id,
                "user_id": UUID(data.user_id),
                "name": data.name,
                "data_source_id": UUID(data.data_source_id),
                "schema_name": data.schema_name,
                "table_name": data.table_name,
            },
        )
        return str(project_id)

    async def get_by_id(self, project_id: str, user_id: str) -> Row | None:
        query = text("""
            SELECT id, user_id, data_source_id, name, schema_name, table_name
            FROM projects
            WHERE id = :project_id AND user_id = :user_id
        """)

        result = await self.session.execute(
            query,
            {
                "project_id": UUID(project_id),
                "user_id": UUID(user_id)
            }
        )
        return result.one_or_none()

    async def get_projects_list(self, user_id: str) -> list[Row]:
        query = text("""
            SELECT
                projects.id,
                projects.data_source_id,
                projects.name,
                projects.schema_name,
                projects.table_name,
                COALESCE(
                    data_sources.file_name,
                    projects.schema_name || '.' || projects.table_name
                ) AS source_name,
                latest_run.quality_score,
                COALESCE(latest_run.finished_at, latest_run.started_at) AS last_run_at,
                latest_run.status AS last_run_status,
                latest_run.errors_count
            FROM projects
            JOIN data_sources
                ON data_sources.id = projects.data_source_id
            LEFT JOIN runs AS latest_run
                ON latest_run.id = (
                    SELECT runs.id
                    FROM runs
                    WHERE runs.project_id = projects.id
                    ORDER BY runs.started_at DESC, runs.id DESC
                    LIMIT 1
                )
            WHERE projects.user_id = :user_id
            ORDER BY projects.created_at DESC
        """)

        result = await self.session.execute(
            query,
            {
                "user_id": UUID(user_id)
            }
        )
        return result.all()
