from uuid import UUID

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

    async def create_file(
        self,
        source_id: str,
        file_name: str,
        file_size_bytes: int,
        file_format: str,
    ) -> None:
        await self.session.execute(
            text("""
                INSERT INTO data_sources (id, type, file_name, file_size_bytes, file_format)
                VALUES (:id, 'FILE', :file_name, :file_size_bytes, :file_format)
            """),
            {
                "id": UUID(source_id),
                "file_name": file_name,
                "file_size_bytes": file_size_bytes,
                "file_format": file_format,
            },
        )

    async def get_by_id(self, source_id: str):
        result = await self.session.execute(
            text("""
                SELECT id, type, file_name, file_size_bytes, file_format
                FROM data_sources
                WHERE id = :id
            """),
            {"id": UUID(source_id)},
        )
        return result.mappings().first()

    async def get_data_source_type(self, source_id: str) -> str | None:
        result = await self.session.execute(
            text("""
                SELECT type
                FROM data_sources
                WHERE id = :id
            """),
            {"id": UUID(source_id)},
        )
        data_source_type = result.scalar_one_or_none()
        if data_source_type is None:
            return None

        return str(data_source_type)
