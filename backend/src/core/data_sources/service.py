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


class DataSourceService:
    def __init__(
        self,
        data_source_reposisory: DataSourceRepository
    ) -> None:
        self.data_source_repo = data_source_reposisory
        self.external_client = PostgresClient()  # TODO: не забыть потом убрать при добавлении других субд

    async def create(self, data: DataSourceCreationDTO) -> str:
        await self.external_client.connect(
            host=data.host,
            port=data.port,
            db_name=data.db_name,
            user=data.username,
            password=data.password,
        )

        return await self.data_source_repo.create(data)

    async def get_tables(
        self,
        source_id: str
    ) -> DataSourceTablesResponseDTO:
        creds = await self._get_data_source_creds_or_raise(source_id)

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

    async def _get_data_source_creds_or_raise(
        self,
        source_id: str
    ) -> DataSourceCredsDTO:
        creds = await self.data_source_repo.get_data_source_creds(source_id)
        if creds is None:
            raise DataSourceNotFoundException(
                f"Источник данных с id: {source_id} не найден"
            )

        return DataSourceCredsDTO(
                host=creds.host,
                port=creds.port,
                db_name=creds.db_name,
                user=creds.username,
                password=creds.password_encrypted
            )
