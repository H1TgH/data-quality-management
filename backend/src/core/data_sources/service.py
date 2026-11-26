from dataclasses import asdict

from core.data_sources.entities import (
    DataSourceCreationDTO,
    DataSourceCredsDTO,
    DataSourceTablesResponseDTO,
)
from core.data_sources.exceptions import (
    DataSourceNotFoundException,
)
from infrastructure.database.repositories.data_source import DataSourceRepository
from infrastructure.external_databases.postgres_client import PostgresClient
from infrastructure.security.security import security_instance


class DataSourceService:
    def __init__(
        self,
        data_source_repository: DataSourceRepository
    ) -> None:
        self.data_source_repo = data_source_repository
        self.external_client = PostgresClient()  # TODO: не забыть потом убрать при добавлении других субд

    async def create(self, data: DataSourceCreationDTO) -> str:
        await self.external_client.connect(
            host=data.host,
            port=data.port,
            db_name=data.db_name,
            user=data.username,
            password=data.password,
        )

        encrypted_password = security_instance.encrypt(data.password)
        data.password = encrypted_password  # TODO подумать над проблемой мутации дто
        return await self.data_source_repo.create(data)

    async def create_file(
        self,
        source_id: str,
        file_name: str,
        file_size_bytes: int,
        file_format: str,
    ) -> None:
        await self.data_source_repo.create_file(
            source_id=source_id,
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            file_format=file_format,
        )

    async def get_tables(
        self,
        source_id: str
    ) -> DataSourceTablesResponseDTO:
        creds = await self.get_data_source_creds(source_id)
        tables = await self.external_client.get_tables(
            timeout=5,
            **asdict(creds)
        )

        return DataSourceTablesResponseDTO(
            tables_full_name=[
                table.table_full_name
                for table in tables
            ],
            total=len(tables)
        )

    async def get_data_source_type(self, source_id: str) -> str | None:
        return await self.data_source_repo.get_data_source_type(source_id)

    async def get_data_source_creds(
        self,
        source_id: str
    ) -> DataSourceCredsDTO:
        creds = await self.data_source_repo.get_data_source_creds(source_id)
        if creds is None:
            raise DataSourceNotFoundException(
                f"Источник данных с id: {source_id} не найден"
            )

        decrypted_password = security_instance.decrypt(creds.password_encrypted)

        return DataSourceCredsDTO(
            host=creds.host,
            port=creds.port,
            db_name=creds.db_name,
            user=creds.username,
            password=decrypted_password,
        )
