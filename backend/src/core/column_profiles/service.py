from dataclasses import asdict

from core.column_profiles.entities import (
    ColumnProfileDTO,
    TableProfileDTO,
)
from core.data_sources.entities import DataSourceCredsDTO
from core.data_sources.enums import DataSourceTypeEnum
from core.data_sources.exceptions import DataSourceNotFoundException
from core.data_sources.service import DataSourceService
from core.data_sources.staging import STAGING_SCHEMA, staging_table_name
from infrastructure.external_databases.postgres_client import PostgresClient


class ColumnProfileService:
    def __init__(
        self,
        data_source_service: DataSourceService,
        external_client: PostgresClient,
        staging_credentials: DataSourceCredsDTO,
    ) -> None:
        self.data_source_service = data_source_service
        self.external_client = external_client
        self.staging_credentials = staging_credentials

    async def profile_table(
        self,
        source_id: str,
        schema: str,
        table_name: str,
        user_id: str,
    ) -> TableProfileDTO:
        source_type = await self.data_source_service.get_data_source_type(source_id, user_id)
        if source_type != DataSourceTypeEnum.DB:
            raise DataSourceNotFoundException(
                f"Источник данных с id: {source_id} типа БД не найден"
            )

        creds = await self.data_source_service.get_data_source_creds(source_id, user_id)

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

    async def profile_file(self, source_id: str, user_id: str) -> TableProfileDTO:
        source_type = await self.data_source_service.get_data_source_type(source_id, user_id)
        if source_type != DataSourceTypeEnum.FILE:
            raise DataSourceNotFoundException(
                f"Файловый источник с id: {source_id} не найден"
            )

        columns, statistics = await self.external_client.profile_table(
            **asdict(self.staging_credentials),
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
            table_name=staging_table_name(source_id),
            total_rows=total_rows,
            columns=profiles,
        )
