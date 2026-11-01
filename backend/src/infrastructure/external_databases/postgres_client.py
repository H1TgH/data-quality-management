import asyncpg

from core.column_profiles.entities import ColumnMetadataDTO
from core.data_sources.entities import DataSourceTablesDTO
from core.data_sources.exceptions import (
    DataSourceAuthException,
    DataSourceConfigurationException,
    DataSourceNetworkException,
    DataSourceTimeoutException,
    DataSourceUnavailableException,
)


class PostgresClient:
    NUMERIC_TYPES = {
        "smallint",
        "integer",
        "bigint",
        "numeric",
        "decimal",
        "real",
        "double precision",
    }

    DATE_TYPES = {
        "date",
        "timestamp without time zone",
        "timestamp with time zone",
        "time without time zone",
        "time with time zone",
    }

    async def connect(
        self,
        host: str,
        port: int,
        db_name: str,
        user: str,
        password: str,
        timeout: float = 10,
    ) -> None:
        conn = await self._connect(
            host, port, db_name, user, password, timeout
        )
        await conn.close()

    async def get_tables(
        self,
        host: str,
        port: int,
        db_name: str,
        user: str,
        password: str,
        timeout: float = 10,
    ) -> list[DataSourceTablesDTO]:

        conn = await self._connect(
            host, port, db_name, user, password, timeout
        )

        try:
            rows = await conn.fetch("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_type = 'BASE TABLE'
                    AND table_schema NOT IN (
                        'pg_catalog',
                        'information_schema'
                    )
                ORDER BY table_schema, table_name;
            """)

            return [
                DataSourceTablesDTO(
                    table_schema=row["table_schema"],
                    table_name=row["table_name"],
                )
                for row in rows
            ]

        finally:
            await conn.close()

    async def get_columns(
        self,
        conn: asyncpg.Connection,
        schema: str,
        table_name: str,
    ) -> list[ColumnMetadataDTO]:

        rows = await conn.fetch(
            """
            SELECT
                column_name,
                data_type,
                ordinal_position
            FROM information_schema.columns
            WHERE table_schema = $1
                AND table_name = $2
            ORDER BY ordinal_position;
            """,
            schema,
            table_name,
        )

        return [
            ColumnMetadataDTO(
                name=row["column_name"],
                data_type=row["data_type"],
                ordinal_position=row["ordinal_position"],
            )
            for row in rows
        ]

    async def profile_table(
        self,
        host: str,
        port: int,
        db_name: str,
        user: str,
        password: str,
        schema: str,
        table_name: str,
        timeout: float = 10,
    ) -> tuple[list[ColumnMetadataDTO], asyncpg.Record]:

        conn = await self._connect(
            host, port, db_name, user, password, timeout
        )

        try:
            columns = await self.get_columns(
                conn=conn,
                schema=schema,
                table_name=table_name,
            )

            if not columns:
                raise ValueError(
                    f"Таблица {schema}.{table_name} не найдена"
                )

            query = self._build_profile_query(
                columns=columns,
                schema=schema,
                table_name=table_name,
            )

            statistics = await conn.fetchrow(query)

            return columns, statistics

        finally:
            await conn.close()

    def _build_profile_query(
        self,
        columns: list[ColumnMetadataDTO],
        schema: str,
        table_name: str,
    ) -> str:

        schema_identifier = self._quote_identifier(schema)
        table_identifier = self._quote_identifier(table_name)

        select_parts = [
            "COUNT(*) AS total_rows",
        ]

        for index, column in enumerate(columns):
            column_identifier = self._quote_identifier(column.name)

            select_parts.append(
                f"COUNT({column_identifier}) AS filled_{index}"
            )

            if column.data_type in self.NUMERIC_TYPES | self.DATE_TYPES:
                select_parts.extend([
                    f"MIN({column_identifier}) AS min_{index}",
                    f"MAX({column_identifier}) AS max_{index}",
                ])

        select_clause = ",\n".join(select_parts)

        return f"""
            SELECT
                {select_clause}
            FROM (
                SELECT *
                FROM {schema_identifier}.{table_identifier}
                LIMIT 100000
            ) AS sampled;
        """

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        return '"' + identifier.replace('"', '""') + '"'

    async def _connect(
        self,
        host: str,
        port: int,
        db_name: str,
        user: str,
        password: str,
        timeout: float = 10,
    ) -> asyncpg.Connection:

        try:
            return await asyncpg.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=db_name,
                timeout=timeout,
            )

        except TimeoutError as exc:
            raise DataSourceTimeoutException(
                "Превышено время ожидания подключения"
            ) from exc

        except OSError as exc:
            raise DataSourceNetworkException(
                "Не удалось установить соединение с сервером"
            ) from exc

        except (
            asyncpg.InvalidPasswordError,
            asyncpg.InvalidAuthorizationSpecificationError,
        ) as exc:
            raise DataSourceAuthException(
                "Ошибка аутентификации в базе данных"
            ) from exc

        except asyncpg.InvalidCatalogNameError as exc:
            raise DataSourceConfigurationException(
                "Указанная база данных не существует"
            ) from exc

        except asyncpg.CannotConnectNowError as exc:
            raise DataSourceUnavailableException(
                "Сервер базы данных временно недоступен"
            ) from exc
