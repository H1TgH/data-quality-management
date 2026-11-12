from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ProjectRepository:
    DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"
    DEFAULT_USER_EMAIL = "system@localhost"

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        data_source_id: str,
        name: str,
        schema_name: str,
        table_name: str,
    ) -> str:
        user_id = await self.session.scalar(
            text("""
                INSERT INTO users (id, email)
                VALUES (:id, :email)
                ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
                RETURNING id
            """),
            {
                "id": UUID(self.DEFAULT_USER_ID),
                "email": self.DEFAULT_USER_EMAIL,
            },
        )
        project_id = uuid4()
        await self.session.execute(
            text("""
                INSERT INTO projects (id, user_id, name, data_source_id, schema_name, table_name)
                VALUES (:id, :user_id, :name, :data_source_id, :schema_name, :table_name)
            """),
            {
                "id": project_id,
                "user_id": user_id,
                "name": name,
                "data_source_id": UUID(data_source_id),
                "schema_name": schema_name,
                "table_name": table_name,
            },
        )
        return str(project_id)
