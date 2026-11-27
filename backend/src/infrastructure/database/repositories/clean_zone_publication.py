from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class CleanZonePublicationRepository:
    def __init__(
        self,
        session: AsyncSession
    ) -> None:
        self.session = session

    async def create(
        self,
        project_id: str,
        run_id: str,
        user_id: str,
        view_schema: str,
        view_name: str,
        view_sql: str,
    ) -> str:
        publication_id = uuid4()
        await self.session.execute(
            text("""
                INSERT INTO clean_zone_publications (
                    id, project_id, run_id, user_id, view_schema, view_name, view_sql
                )
                VALUES (
                    :id, :project_id, :run_id, :user_id,
                    :view_schema, :view_name, :view_sql
                )
            """),
            {
                "id": publication_id,
                "project_id": project_id,
                "run_id": run_id,
                "user_id": user_id,
                "view_schema": view_schema,
                "view_name": view_name,
                "view_sql": view_sql,
            },
        )
        return str(publication_id)
