import asyncpg

from core.data_sources.entities import DataSourceTablesDTO
from core.data_sources.exceptions import (
    DataSourceAuthException,
    DataSourceConfigurationException,
    DataSourceNetworkException,
    DataSourceTimeoutException,
    DataSourceUnavailableException,
)


class PostgresClient:
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
                DataSourceTablesDTO(table_schema=row["table_schema"], table_name=row["table_name"])
                for row in rows
            ]

        finally:
            await conn.close()

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
