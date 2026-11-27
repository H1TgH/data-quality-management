from uuid import uuid4

from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from core.rules.enums import RuleTypeEnum


class ErrorLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        run_id: str,
        rule_id: str,
        rule_type: RuleTypeEnum,
        target_columns: list[str],
        row_data: dict,
    ) -> None:
        query = text("""
            INSERT INTO error_log (
                id, run_id, rule_id, rule_type, target_columns, row_data
            )
            VALUES (
                :id, :run_id, :rule_id, :rule_type, :target_columns, :row_data
            )
        """).bindparams(
            bindparam("row_data", type_=JSONB)
        )

        await self.session.execute(
            query,
            {
                "id": uuid4(),
                "run_id": run_id,
                "rule_id": rule_id,
                "rule_type": rule_type,
                "target_columns": target_columns,
                "row_data": row_data,
            },
        )

    async def get_groups(
        self,
        run_id: str
    ) -> list:
        result = await self.session.execute(
            text("""
                SELECT error_log.rule_id, rules.name AS rule_name,
                       error_log.rule_type, rules.action,
                       field_name, COUNT(*) AS rows_count,
                       rules.params AS expected_condition
                FROM error_log
                LEFT JOIN rules ON rules.id = error_log.rule_id
                CROSS JOIN LATERAL unnest(error_log.target_columns)
                    AS target_fields(field_name)
                WHERE error_log.run_id = :run_id
                  AND error_log.status = 'OPEN'
                GROUP BY error_log.rule_id, rules.name, error_log.rule_type,
                         rules.action, field_name, rules.params
                ORDER BY field_name, rules.name
            """),
            {"run_id": run_id},
        )
        return result.all()

    async def get_group_rows(
        self,
        run_id: str,
        rule_id: str,
        field_name: str,
        offset: int,
        limit: int,
    ) -> tuple[list, int]:
        result = await self.session.execute(
            text("""
                SELECT id, row_data, status
                FROM error_log
                WHERE run_id = :run_id
                  AND rule_id = :rule_id
                  AND :field_name = ANY(target_columns)
                  AND status = 'OPEN'
                ORDER BY id
                OFFSET :offset LIMIT :limit
            """),
            {
                "run_id": run_id,
                "rule_id": rule_id,
                "field_name": field_name,
                "offset": offset,
                "limit": limit,
            },
        )
        rows = result.all()
        count = await self.session.execute(
            text("""
                SELECT COUNT(*)
                FROM error_log
                WHERE run_id = :run_id
                  AND rule_id = :rule_id
                  AND :field_name = ANY(target_columns)
                  AND status = 'OPEN'
            """),
            {"run_id": run_id, "rule_id": rule_id, "field_name": field_name},
        )
        return rows, count.scalar_one()

    async def get_export_rows(self, run_id: str) -> list:
        result = await self.session.execute(
            text("""
                SELECT rules.name AS rule_name, error_log.rule_type,
                       error_log.target_columns, error_log.row_data
                FROM error_log
                LEFT JOIN rules ON rules.id = error_log.rule_id
                WHERE error_log.run_id = :run_id
                  AND error_log.status = 'OPEN'
                ORDER BY rules.name, error_log.id
            """),
            {"run_id": run_id},
        )
        return result.all()

    async def mark_row_valid(self, run_id: str, error_id: str) -> bool:
        result = await self.session.execute(
            text("""
                WITH marked AS (
                    UPDATE error_log
                    SET status = 'MARKED_VALID'
                    WHERE run_id = :run_id
                      AND row_data = (
                          SELECT row_data FROM error_log
                          WHERE id = :error_id AND run_id = :run_id
                      )
                    RETURNING id, row_data
                ), failed_candidates AS (
                    SELECT row_data FROM error_log
                    WHERE run_id = :run_id AND status = 'OPEN'
                    UNION
                    SELECT row_data FROM cleaned_rows
                    WHERE run_id = :run_id
                ), failed_rows AS (
                    SELECT row_data FROM failed_candidates
                    EXCEPT
                    (
                        SELECT row_data FROM error_log
                        WHERE run_id = :run_id AND status = 'MARKED_VALID'
                        UNION
                        SELECT row_data FROM marked
                    )
                ), metrics AS (
                    SELECT COUNT(*) AS failed_count FROM failed_rows
                )
                UPDATE runs
                SET quality_score = CASE
                    WHEN rows_total > 0 THEN
                        100.0 * (rows_total - metrics.failed_count) / rows_total
                    ELSE NULL
                END,
                    errors_count = (
                        SELECT COUNT(*) FROM error_log
                        WHERE run_id = :run_id AND status = 'OPEN'
                    )
                FROM metrics
                WHERE runs.id = :run_id
                RETURNING (SELECT id FROM marked LIMIT 1) AS marked_id
            """),
            {"run_id": run_id, "error_id": error_id},
        )
        row = result.first()
        return row is not None and row.marked_id is not None
