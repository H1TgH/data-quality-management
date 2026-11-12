import asyncio
import logging
from collections.abc import Iterator
from itertools import islice
from typing import Any

import asyncpg

from core.data_sources.exceptions import EmptyFileException, TooManyRowsException
from core.data_sources.staging import STAGING_SCHEMA


logger = logging.getLogger(__name__)


INT_RE = "^-?(0|[1-9][0-9]{0,17})$"
FLOAT_RE = "^-?(0|[1-9][0-9]*)([.,][0-9]+)?$"
DATE_RE = "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
DATE_RU_RE = "^[0-9]{2}[.][0-9]{2}[.][0-9]{4}$"
TIMESTAMP_RE = (
    "^[0-9]{4}-[0-9]{2}-[0-9]{2}[ T][0-9]{2}:[0-9]{2}"
    "(:[0-9]{2}([.][0-9]+)?)?$"
)


def _q(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _take(rows: Iterator, size: int) -> list:
    return list(islice(rows, size))


class StagingLoader:
    BATCH_SIZE = 20_000
    MAX_ROWS = 1_000_000

    def __init__(self, connection_params: dict[str, Any]) -> None:
        self.connection_params = connection_params

    async def load(
        self,
        table_name: str,
        headers: list[str],
        rows: Iterator[list[str | None]],
    ) -> int:
        conn = await asyncpg.connect(**self.connection_params)
        table = f"{_q(STAGING_SCHEMA)}.{_q(table_name)}"

        try:
            await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {_q(STAGING_SCHEMA)}")
            columns_sql = ", ".join(f"{_q(h)} text" for h in headers)
            await conn.execute(f"CREATE TABLE {table} ({columns_sql})")

            try:
                total = await self._copy_rows(conn, table_name, headers, rows)
                await self._cast_columns(conn, table, headers)
            except BaseException:
                await conn.execute(f"DROP TABLE IF EXISTS {table}")
                raise

            return total
        finally:
            await conn.close()

    async def drop(self, table_name: str) -> None:
        conn = await asyncpg.connect(**self.connection_params)
        try:
            await conn.execute(
                f"DROP TABLE IF EXISTS {_q(STAGING_SCHEMA)}.{_q(table_name)}"
            )
        finally:
            await conn.close()

    async def _copy_rows(
        self,
        conn: asyncpg.Connection,
        table_name: str,
        headers: list[str],
        rows: Iterator[list[str | None]],
    ) -> int:
        total = 0

        while True:
            batch = await asyncio.to_thread(_take, rows, self.BATCH_SIZE)
            if not batch:
                break

            total += len(batch)
            if total > self.MAX_ROWS:
                raise TooManyRowsException(
                    f"В файле больше {self.MAX_ROWS:,} строк".replace(",", " ")
                )

            await conn.copy_records_to_table(
                table_name,
                records=batch,
                columns=headers,
                schema_name=STAGING_SCHEMA,
            )

        if total == 0:
            raise EmptyFileException("В файле нет строк с данными")

        return total

    async def _cast_columns(
        self,
        conn: asyncpg.Connection,
        table: str,
        headers: list[str],
    ) -> None:
        parts = []
        for i, header in enumerate(headers):
            value = f"btrim({_q(header)})"
            parts.append(
                f"count(*) FILTER (WHERE {value} <> '') AS filled_{i}, "
                f"count(*) FILTER (WHERE {value} ~ '{INT_RE}') AS int_{i}, "
                f"count(*) FILTER (WHERE {value} ~ '{FLOAT_RE}') AS float_{i}, "
                f"count(*) FILTER (WHERE {value} ~ '{DATE_RE}') AS date_{i}, "
                f"count(*) FILTER (WHERE {value} ~ '{DATE_RU_RE}') AS date_ru_{i}, "
                f"count(*) FILTER (WHERE {value} ~ '{TIMESTAMP_RE}') AS ts_{i}"
            )

        stats = await conn.fetchrow(f"SELECT {', '.join(parts)} FROM {table}")

        casts: dict[str, tuple[str, str]] = {}
        for i, header in enumerate(headers):
            filled = stats[f"filled_{i}"]
            if not filled:
                continue

            trimmed = f"nullif(btrim({_q(header)}), '')"

            if stats[f"int_{i}"] == filled:
                casts[header] = ("bigint", f"{trimmed}::bigint")
            elif stats[f"float_{i}"] == filled:
                casts[header] = ("numeric", f"replace({trimmed}, ',', '.')::numeric")
            elif stats[f"date_{i}"] == filled:
                casts[header] = ("date", f"{trimmed}::date")
            elif stats[f"date_ru_{i}"] == filled:
                casts[header] = ("date", f"to_date({trimmed}, 'DD.MM.YYYY')")
            elif stats[f"date_{i}"] + stats[f"ts_{i}"] == filled:
                casts[header] = ("timestamp", f"{trimmed}::timestamp")

        await self._apply_casts(conn, table, casts)

    async def _apply_casts(
        self,
        conn: asyncpg.Connection,
        table: str,
        casts: dict[str, tuple[str, str]],
    ) -> None:
        if not casts:
            return

        def alter_sql(items: list[tuple[str, tuple[str, str]]]) -> str:
            clauses = ", ".join(
                f"ALTER COLUMN {_q(name)} TYPE {pg_type} USING {using}"
                for name, (pg_type, using) in items
            )
            return f"ALTER TABLE {table} {clauses}"

        try:
            await conn.execute(alter_sql(list(casts.items())))
        except asyncpg.PostgresError:
            for item in casts.items():
                try:
                    await conn.execute(alter_sql([item]))
                except asyncpg.PostgresError:
                    logger.warning("Колонка %s осталась текстовой", item[0])
