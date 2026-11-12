from uuid import uuid4

from sqlalchemy import Row, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from core.rules.entities import RuleCreationDTO


class RuleRepository:
    def __init__(
        self,
        session: AsyncSession
    ) -> None:
        self.session = session

    async def create_rule(
        self,
        rule_data: RuleCreationDTO
    ) -> str:
        id = uuid4()

        query = text("""
            INSERT INTO rules (id, project_id, name, rule_type, target_columns, params, action, is_active)
            VALUES (:id, :project_id, :name, :rule_type, :target_columns, :params, :action, :is_active)
            RETURNING id
        """).bindparams(
            bindparam("params", type_=JSONB)
        )

        result = await self.session.execute(
            query,
            {
                "id": id,
                "project_id": rule_data.project_id,
                "name": rule_data.name,
                "rule_type": rule_data.rule_type,
                "target_columns": rule_data.target_columns,
                "params": rule_data.params,
                "action": rule_data.action,
                "is_active": rule_data.is_active,
            }
        )
        return str(result.scalar_one())

    async def get_data_source_id(
        self,
        project_id: str
    ) -> str | None:
        query = text("""
            SELECT data_source_id
            FROM projects
            WHERE id = :project_id
        """)

        result = await self.session.execute(
            query,
            {
                "project_id": project_id
            }
        )
        data_source_id = result.scalar_one_or_none()
        if data_source_id is None:
            return None

        return str(data_source_id)

    async def get_rules_list(
        self,
        project_id: str
    ) -> list[Row]:
        query = text("""
            SELECT id, project_id, name, rule_type, target_columns, params, action, is_active, created_at, updated_at
            FROM rules
            WHERE project_id = :project_id
            ORDER BY created_at, id
        """)

        result = await self.session.execute(
            query,
            {
                "project_id": project_id
            }
        )
        return result.all()

    async def get_rule(
        self,
        project_id: str,
        rule_id: str
    ) -> Row | None:
        query = text("""
            SELECT id, project_id, name, rule_type, target_columns, params, action, is_active, created_at, updated_at
            FROM rules
            WHERE project_id = :project_id
            AND id = :rule_id
        """)

        result = await self.session.execute(
            query,
            {
                "project_id": project_id,
                "rule_id": rule_id,
            },
        )
        rule = result.one_or_none()
        return rule

    async def update_rule(
        self,
        project_id: str,
        rule_id: str,
        rule_data: RuleCreationDTO
    ) -> Row | None:
        query = text("""
            UPDATE rules
            SET name = :name,
                rule_type = :rule_type,
                target_columns = :target_columns,
                params = :params,
                action = :action,
                is_active = :is_active,
                updated_at = now()
            WHERE project_id = :project_id
            AND id = :rule_id
            RETURNING id, project_id, name, rule_type, target_columns, params, action,
                      is_active, created_at, updated_at
        """).bindparams(
            bindparam("params", type_=JSONB)
        )

        result = await self.session.execute(
            query,
            {
                "project_id": project_id,
                "rule_id": rule_id,
                "name": rule_data.name,
                "rule_type": rule_data.rule_type,
                "target_columns": rule_data.target_columns,
                "params": rule_data.params,
                "action": rule_data.action,
                "is_active": rule_data.is_active,
            }
        )
        return result.one_or_none()

    async def delete_rule(
        self,
        project_id: str,
        rule_id: str
    ) -> bool:
        query = text("""
            DELETE FROM rules
            WHERE project_id = :project_id
            AND id = :rule_id
            RETURNING id
        """)

        result = await self.session.execute(
            query,
            {
                "project_id": project_id,
                "rule_id": rule_id,
            }
        )
        return result.scalar_one_or_none() is not None

    async def set_rule_is_active(
        self,
        project_id: str,
        rule_id: str,
        is_active: bool
    ) -> Row | None:
        query = text("""
            UPDATE rules
            SET is_active = :is_active,
                updated_at = now()
            WHERE project_id = :project_id
            AND id = :rule_id
            RETURNING id, project_id, name, rule_type, target_columns, params, action, is_active, created_at, updated_at
        """)

        result = await self.session.execute(
            query,
            {
                "project_id": project_id,
                "rule_id": rule_id,
                "is_active": is_active,
            }
        )
        return result.one_or_none()
