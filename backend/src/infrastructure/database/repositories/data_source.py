from uuid import uuid4

from sqlalchemy import Row, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.data_sources.entities import DataSourceCreationDTO


class DataSourceRepository:
    def __init__(
            self,
            session: AsyncSession
        ) -> None:
        self.session = session

    async def create(
        self,
        data_sources_creation_dto: DataSourceCreationDTO
    ) -> str:
        id = uuid4()
        query = text("""
            INSERT INTO data_sources (id, type, host, port, db_name, username, password_encrypted)
            VALUES (:id, :type, :host, :port, :db_name, :username, :password)
            RETURNING id
        """)

        result = await self.session.execute(
            query,
            {
                "id": id,
                "type": data_sources_creation_dto.type,
                "host": data_sources_creation_dto.host,
                "port": data_sources_creation_dto.port,
                "db_name": data_sources_creation_dto.db_name,
                "username": data_sources_creation_dto.username,
                "password": data_sources_creation_dto.password
            }
        )
        return str(result.scalar_one())

    async def get_data_source_creds(
        self,
        source_id: str
    ) -> Row | None:
        query = text("""
            SELECT host, port, db_name, username, password_encrypted
            FROM data_sources
            WHERE id = :source_id
        """)

        result = await self.session.execute(
            query,
            {"source_id": source_id}
        )
        return result.one_or_none()
