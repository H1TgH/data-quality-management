from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.runs.enums import RunStatusEnum, RunTriggerEnum


class RunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, project_id: str, trigger: RunTriggerEnum) -> str:
        run_id = uuid4()
        result = await self.session.execute(
            text("""
                INSERT INTO runs (id, project_id, trigger, status)
                VALUES (:id, :project_id, :trigger, :status)
                RETURNING id
            """),
            {
                "id": run_id,
                "project_id": project_id,
                "trigger": trigger,
                "status": RunStatusEnum.RUNNING,
            },
        )
        return str(result.scalar_one())

    async def finish(
        self,
        run_id: str,
        status: RunStatusEnum,
        rows_total: int,
        rows_removed: int | None,
        errors_count: int,
        quality_score: float | None,
    ) -> None:
        await self.session.execute(
            text("""
                UPDATE runs
                SET status = :status,
                    finished_at = now(),
                    rows_total = :rows_total,
                    rows_removed = :rows_removed,
                    errors_count = :errors_count,
                    quality_score = :quality_score
                WHERE id = :run_id
            """),
            {
                "run_id": run_id,
                "status": status,
                "rows_total": rows_total,
                "rows_removed": rows_removed,
                "errors_count": errors_count,
                "quality_score": quality_score,
            },
        )

    async def get_runs(self, project_id: str) -> list:
        result = await self.session.execute(
            text("""
                SELECT id, project_id, trigger, status, started_at, finished_at,
                       rows_total, rows_removed, errors_count, quality_score
                FROM runs
                WHERE project_id = :project_id
                ORDER BY started_at DESC
            """),
            {"project_id": project_id},
        )
        return result.all()

    async def get_run(self, project_id: str, run_id: str):
        result = await self.session.execute(
            text("""
                SELECT id, project_id, trigger, status, started_at, finished_at,
                       rows_total, rows_removed, errors_count, quality_score
                FROM runs
                WHERE project_id = :project_id AND id = :run_id
            """),
            {"project_id": project_id, "run_id": run_id},
        )
        return result.one_or_none()
