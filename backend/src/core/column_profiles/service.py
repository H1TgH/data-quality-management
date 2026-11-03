from dataclasses import asdict

from core.column_profiles.entities import (
    ColumnProfileDTO,
    TableProfileDTO,
)
from core.data_sources.entities import DataSourceCredsDTO
from core.data_sources.exceptions import DataSourceNotFoundException
from core.data_sources.staging import STAGING_SCHEMA, staging_table_name
from infrastructure.database.repositories.data_source import DataSourceRepository
from infrastructure.external_databases.postgres_client import PostgresClient
from settings import settings


class ColumnProfileService:
    def __init__(
        self,
        data_source_repository: DataSourceRepository,
        external_client: PostgresClient,
    ) -> None:
        self.data_source_repo = data_source_repository
        self.external_client = external_client

    async def profile_table(
        self,
        source_id: str,
        schema: str,
        table_name: str,
    ) -> TableProfileDTO:

        creds = await self._get_data_source_creds_or_raise(source_id)

        columns, statistics = await self.external_client.profile_table(
            **asdict(creds),
            schema=schema,
            table_name=table_name,
        )

        total_rows = statistics["total_rows"]

        profiles = [
            ColumnProfileDTO(
                column_name=column.name,
                data_type=column.data_type,
                total_rows=total_rows,
                filled_rows=statistics[f"filled_{index}"],
                completeness=(
                    statistics[f"filled_{index}"] / total_rows * 100
                    if total_rows else 0
                ),
                min_value=statistics.get(f"min_{index}"),
                max_value=statistics.get(f"max_{index}"),
            )
            for index, column in enumerate(columns)
        ]

        return TableProfileDTO(
            table_name=table_name,
            total_rows=total_rows,
            columns=profiles,
        )

    async def _get_data_source_creds_or_raise(
        self,
        source_id: str,
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

    async def profile_file(self, source_id: str) -> TableProfileDTO:
        source = await self.data_source_repo.get_by_id(source_id)

        if source is None or source["type"] != "FILE":
            raise DataSourceNotFoundException(
                f"Файловый источник с id: {source_id} не найден"
            )

        columns, statistics = await self.external_client.profile_table(
            host=settings.db.host,
            port=settings.db.port,
            db_name=settings.db.db,
            user=settings.db.user,
            password=settings.db.password.get_secret_value(),
            schema=STAGING_SCHEMA,
            table_name=staging_table_name(source_id),
        )

        total_rows = statistics["total_rows"]

        profiles = [
            ColumnProfileDTO(
                column_name=column.name,
                data_type=column.data_type,
                total_rows=total_rows,
                filled_rows=statistics[f"filled_{index}"],
                completeness=(
                    statistics[f"filled_{index}"] / total_rows * 100
                    if total_rows else 0
                ),
                min_value=statistics.get(f"min_{index}"),
                max_value=statistics.get(f"max_{index}"),
            )
            for index, column in enumerate(columns)
        ]

        return TableProfileDTO(
            table_name="1123",
            total_rows=total_rows,
            columns=profiles,
        )
