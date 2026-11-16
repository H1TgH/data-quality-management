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
