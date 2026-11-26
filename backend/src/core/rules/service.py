from sqlalchemy import Row

from core.projects.service import ProjectService
from core.rules.entities import RuleCreationDTO, RuleReadDTO, RulesListResponseDTO
from core.rules.exceptions import RuleNotFoundException
from infrastructure.database.repositories.rule import RuleRepository


class RuleService:
    def __init__(
        self,
        rule_repository: RuleRepository,
        project_service: ProjectService,
    ) -> None:
        self.rule_repo = rule_repository
        self.project_service = project_service

    async def create_rule(
        self,
        rule_data: RuleCreationDTO,
        user_id: str,
    ) -> str:
        await self._get_project_or_raise(rule_data.project_id, user_id)

        await self._validate_rule(rule_data)

        rule_id = await self.rule_repo.create_rule(rule_data)
        return rule_id

    async def get_rules_list(
        self,
        project_id: str,
        user_id: str,
    ) -> RulesListResponseDTO:  # TODO добавить пагинацию
        await self._get_project_or_raise(project_id, user_id)

        rules = await self.rule_repo.get_rules_list(project_id)

        return RulesListResponseDTO(
            items=[
                self._build_rule_read_dto(rule)
                for rule in rules
            ],
            total=len(rules)
        )

    async def get_rule(
        self,
        project_id: str,
        rule_id: str,
        user_id: str,
    ) -> RuleReadDTO | None:
        await self._get_project_or_raise(project_id, user_id)

        rule = await self._get_rule_or_raise(project_id, rule_id)

        return rule

    async def update_rule(
        self,
        project_id: str,
        rule_id: str,
        rule_data: RuleCreationDTO,
        user_id: str,
    ) -> RuleReadDTO:
        await self._get_project_or_raise(project_id, user_id)

        await self._validate_rule(rule_data)

        rule = await self.rule_repo.update_rule(project_id, rule_id, rule_data)
        if not rule:
            raise RuleNotFoundException(f"Правило {rule_id} не найдено")

        return self._build_rule_read_dto(rule)

    async def delete_rule(
        self,
        project_id: str,
        rule_id: str,
        user_id: str,
    ) -> None:
        await self._get_project_or_raise(project_id, user_id)

        rule_is_deleted = await self.rule_repo.delete_rule(project_id, rule_id)
        if not rule_is_deleted:
            raise RuleNotFoundException(f"Правило {rule_id} не найдено")

    async def set_rule_is_active(
        self,
        project_id: str,
        rule_id: str,
        is_active: bool,
        user_id: str,
    ) -> RuleReadDTO:
        await self._get_project_or_raise(project_id, user_id)

        rule = await self.rule_repo.set_rule_is_active(project_id, rule_id, is_active)
        if not rule:
            raise RuleNotFoundException(f"Правило {rule_id} не найдено")

        return self._build_rule_read_dto(rule)

    async def _get_project_or_raise(
        self,
        project_id: str,
        user_id: str,
    ) -> None:
        await self.project_service.get_project(project_id, user_id)

    async def _get_rule_or_raise(
        self,
        project_id: str,
        rule_id: str
    ) -> RuleReadDTO:
        rule = await self.rule_repo.get_rule(project_id, rule_id)
        if not rule:
            raise RuleNotFoundException(f"Правило {rule_id} не найдено")

        return self._build_rule_read_dto(rule)

    async def _validate_rule(
        self,
        data
    ) -> None:
        return True  # TODO потом добавитть чтобы функция валидировала правило (например у диапазона должно быть 2 граничных числа)  # noqa: E501

    @staticmethod
    def _build_rule_read_dto(
        rule: Row
    ) -> RuleReadDTO:
        return RuleReadDTO(
            id=rule.id,
            project_id=rule.project_id,
            name=rule.name,
            rule_type=rule.rule_type,
            target_columns=rule.target_columns,
            params=rule.params,
            action=rule.action,
            is_active=rule.is_active,
            created_at=rule.created_at
        )
