import json
from dataclasses import asdict
from typing import Any

from core.data_sources.entities import DataSourceCredsDTO
from core.data_sources.enums import DataSourceTypeEnum
from core.data_sources.exceptions import DataSourceNotFoundException
from core.data_sources.service import DataSourceService
from core.projects.service import ProjectService
from core.rules.entities import RuleReadDTO
from core.rules.enums import RuleActionEnum, RuleTypeEnum
from core.rules.service import RuleService
from core.runs.enums import RunStatusEnum, RunTriggerEnum
from core.runs.exceptions import RunPublicationException
from infrastructure.database.repositories.clean_zone_publication import CleanZonePublicationRepository
from infrastructure.database.repositories.cleaned_rows import CleanedRowsRepository
from infrastructure.database.repositories.error_log import ErrorLogRepository
from infrastructure.database.repositories.run import RunRepository
from infrastructure.external_databases.postgres_client import PostgresClient


class RunService:
    def __init__(
        self,
        project_service: ProjectService,
        rule_service: RuleService,
        data_source_service: DataSourceService,
        run_repository: RunRepository,
        error_log_repository: ErrorLogRepository,
        cleaned_rows_repository: CleanedRowsRepository,
        publication_repository: CleanZonePublicationRepository,
        postgres_client: PostgresClient,
        staging_credentials: DataSourceCredsDTO,
    ) -> None:
        self.project_service = project_service
        self.rule_service = rule_service
        self.data_source_service = data_source_service
        self.run_repo = run_repository
        self.error_log_repo = error_log_repository
        self.cleaned_rows_repo = cleaned_rows_repository
        self.publication_repo = publication_repository
        self.pg_client = postgres_client
        self.staging_credentials = staging_credentials

    async def run_check(self, project_id: str, user_id: str) -> dict[str, Any]:
        project = await self.project_service.get_project(project_id, user_id)
        rules_response = await self.rule_service.get_rules_list(project_id, user_id)
        active_rules = self._keep_active_rules(rules_response.items)

        connection_params = await self._get_connection_params(project.data_source_id, user_id)
        table_name = self._get_table_name(project.schema_name, project.table_name)
        conditions = self._build_check_conditions(table_name, active_rules)

        connection = await self.pg_client._connect(**connection_params)
        try:
            async with connection.transaction(
                readonly=True,
            ):
                rows_total = await connection.fetchval(
                    f"SELECT COUNT(*) FROM {table_name}"
                )

                run_id = await self.run_repo.create(
                    project_id=project_id,
                    trigger=RunTriggerEnum.MANUAL,
                )

                failed_rows = set()
                cleaned_rows = set()
                errors_count = 0

                for condition in conditions:
                    records = await connection.fetch(
                        condition["query"],
                        *condition["params"],
                    )
                    for record in records:
                        row_data = record["row_data"]
                        if isinstance(row_data, str):
                            row_data = json.loads(row_data)

                        failed_rows.add(record["row_key"])
                        if condition["rule"].action == RuleActionEnum.AUTO_CLEAN:
                            await self.cleaned_rows_repo.create(
                                run_id=run_id,
                                rule_id=condition["rule"].id,
                                rule_type=condition["rule"].rule_type,
                                target_columns=condition["target_columns"],
                                row_data=row_data,
                            )
                            cleaned_rows.add(record["row_key"])
                        else:
                            await self.error_log_repo.create(
                                run_id=run_id,
                                rule_id=condition["rule"].id,
                                rule_type=condition["rule"].rule_type,
                                target_columns=condition["target_columns"],
                                row_data=row_data,
                            )
                            errors_count += 1

                quality_score = None
                if rows_total:
                    quality_score = (
                        (rows_total - len(failed_rows)) / rows_total * 100
                    )

                await self.run_repo.finish(
                    run_id=run_id,
                    status=RunStatusEnum.SUCCESS,
                    rows_total=rows_total,
                    rows_removed=len(cleaned_rows),
                    errors_count=errors_count,
                    quality_score=quality_score,
                )

                return {
                    "run_id": run_id,
                    "rows_total": rows_total,
                    "rows_removed": len(cleaned_rows),
                    "errors_count": errors_count,
                    "unique_rows_with_violations": len(failed_rows),
                    "quality_score": quality_score,
                }
        finally:
            await connection.close()

    async def get_runs(self, project_id: str, user_id: str):
        await self.project_service.get_project(project_id, user_id)
        runs = await self.run_repo.get_runs(project_id)
        return [dict(run._mapping) for run in runs]

    async def get_quality_trend(self, project_id: str, user_id: str, period: str):
        await self.project_service.get_project(project_id, user_id)
        points = await self.run_repo.get_quality_trend(project_id, period)
        return [dict(point._mapping) for point in points]

    async def get_run(self, project_id: str, run_id: str, user_id: str):
        await self.project_service.get_project(project_id, user_id)
        run = await self.run_repo.get_run(project_id, run_id)
        if run is None:
            return None
        return dict(run._mapping)

    async def get_error_groups(self, project_id: str, run_id: str, user_id: str):
        run = await self.get_run(project_id, run_id, user_id)
        if run is None:
            return None
        groups = await self.error_log_repo.get_groups(run_id)
        return [dict(group._mapping) for group in groups]

    async def get_error_export_rows(self, project_id: str, run_id: str, user_id: str):
        run = await self.get_run(project_id, run_id, user_id)
        if run is None:
            return None
        return await self.error_log_repo.get_export_rows(run_id)

    async def get_error_group_sql(
        self,
        project_id: str,
        run_id: str,
        rule_id: str,
        field_name: str,
        user_id: str,
    ):
        run = await self.get_run(project_id, run_id, user_id)
        if run is None:
            return None

        project = await self.project_service.get_project(project_id, user_id)
        rules_response = await self.rule_service.get_rules_list(project_id, user_id)
        conditions = self._build_check_conditions(
            self._get_table_name(project.schema_name, project.table_name),
            rules_response.items,
        )
        return [
            {"sql": condition["query"], "params": condition["params"]}
            for condition in conditions
            if str(condition["rule"].id) == rule_id
            and field_name in condition["target_columns"]
        ]

    async def publish_to_clean_zone(
        self,
        project_id: str,
        run_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        run = await self.get_run(project_id, run_id, user_id)
        if run is None:
            raise RunPublicationException("Запуск не найден")
        if run["status"] != RunStatusEnum.SUCCESS:
            raise RunPublicationException("Опубликовать можно только завершённый запуск")
        if run["quality_score"] is None or float(run["quality_score"]) < 90:
            raise RunPublicationException(
                "Публикация доступна при оценке качества не ниже 90%"
            )

        project = await self.project_service.get_project(project_id, user_id)
        rules_response = await self.rule_service.get_rules_list(project_id, user_id)
        active_rules = self._keep_active_rules(rules_response.items)
        where_conditions = []
        remove_duplicates = False

        for rule in active_rules:
            if rule.action != RuleActionEnum.AUTO_CLEAN:
                continue

            if rule.rule_type == RuleTypeEnum.UNIQUENESS:
                remove_duplicates = True
            elif rule.rule_type == RuleTypeEnum.NOT_NULL:
                for column in rule.target_columns:
                    if column == "*":
                        where_conditions.append(
                            "NOT EXISTS (SELECT 1 FROM jsonb_each(to_jsonb(source_row)) "
                            "AS source_column WHERE source_column.value = 'null'::jsonb "
                            "OR source_column.value #>> '{}' = '')"
                        )
                    else:
                        quoted_column = self._quote_identifier(column)
                        where_conditions.append(
                            f"source_row.{quoted_column} IS NOT NULL "
                            f"AND BTRIM(source_row.{quoted_column}::text) <> ''"
                        )

        source_credentials = await self._get_connection_params(
            project.data_source_id,
            user_id,
        )
        view_sql = await self.pg_client.publish_clean_view(
            **source_credentials,
            source_schema=project.schema_name or "public",
            table_name=project.table_name,
            view_name=project.table_name,
            where_conditions=where_conditions,
            remove_duplicates=remove_duplicates,
        )
        publication_id = await self.publication_repo.create(
            project_id=project_id,
            run_id=run_id,
            user_id=user_id,
            view_schema="clean",
            view_name=project.table_name,
            view_sql=view_sql,
        )

        return {
            "publication_id": publication_id,
            "view_name": f"clean.{project.table_name}",
            "quality_score": float(run["quality_score"]),
        }

    async def get_error_group_rows(
        self,
        project_id: str,
        run_id: str,
        rule_id: str,
        field_name: str,
        user_id: str,
        offset: int,
        limit: int,
    ):
        run = await self.get_run(project_id, run_id, user_id)
        if run is None:
            return None
        rows, total = await self.error_log_repo.get_group_rows(
            run_id=run_id,
            rule_id=rule_id,
            field_name=field_name,
            offset=offset,
            limit=limit,
        )
        return {"items": [dict(row._mapping) for row in rows], "total": total}

    async def mark_error_row_valid(
        self,
        project_id: str,
        run_id: str,
        error_id: str,
        user_id: str,
    ) -> bool:
        run = await self.get_run(project_id, run_id, user_id)
        if run is None:
            return False
        return await self.error_log_repo.mark_row_valid(run_id, error_id)

    async def _get_connection_params(self, data_source_id: str, user_id: str) -> dict[str, Any]:
        data_source_type = await self.data_source_service.get_data_source_type(data_source_id, user_id)
        if data_source_type == DataSourceTypeEnum.FILE:
            return asdict(self.staging_credentials)

        if data_source_type != DataSourceTypeEnum.DB:
            raise DataSourceNotFoundException(
                f"Источник данных с id: {data_source_id} не найден"
            )

        credentials = await self.data_source_service.get_data_source_creds(data_source_id, user_id)
        return asdict(credentials)

    def _build_check_conditions(
        self,
        table_name: str,
        rules: list[RuleReadDTO],
    ) -> list[dict[str, Any]]:
        conditions = []

        for rule in rules:
            if rule.rule_type == RuleTypeEnum.UNIQUENESS:
                conditions.append({
                    "rule": rule,
                    "target_columns": rule.target_columns,
                    "query": f"""
                        SELECT row_key, row_data
                        FROM (
                            SELECT source_row.ctid::text AS row_key,
                                   to_jsonb(source_row) AS row_data,
                                   ROW_NUMBER() OVER (
                                       PARTITION BY to_jsonb(source_row)
                                       ORDER BY source_row.ctid
                                   ) AS row_number
                            FROM {table_name} AS source_row
                        ) AS source_rows
                        WHERE row_number > 1
                    """,
                    "params": [],
                })
                continue

            if rule.rule_type == RuleTypeEnum.CUSTOM_SQL:
                expression = self._get_rule_param(
                    rule.params,
                    "expression",
                    "formula",
                    "value",
                )
                conditions.append({
                    "rule": rule,
                    "target_columns": rule.target_columns,
                    "query": f"""
                        SELECT source_row.ctid::text AS row_key,
                               to_jsonb(source_row) AS row_data
                        FROM {table_name} AS source_row
                        WHERE NOT ({expression})
                    """,
                    "params": [],
                })
                continue

            for column in rule.target_columns:
                quoted_column = self._quote_identifier(column)
                condition = None
                params = []

                if rule.rule_type == RuleTypeEnum.NOT_NULL:
                    if column == "*":
                        condition = """
                            EXISTS (
                                SELECT 1
                                FROM jsonb_each(to_jsonb(source_row)) AS source_column
                                WHERE source_column.value = 'null'::jsonb
                                   OR source_column.value #>> '{}' = ''
                            )
                        """
                    else:
                        condition = (
                            f"source_row.{quoted_column} IS NULL "
                            f"OR BTRIM(source_row.{quoted_column}::text) = ''"
                        )

                elif rule.rule_type == RuleTypeEnum.REGEX:
                    regex = self._get_rule_param(
                        rule.params,
                        "value",
                        "pattern",
                        "regex",
                    )
                    condition = f"source_row.{quoted_column}::text !~ $1"
                    params = [regex]

                elif rule.rule_type == RuleTypeEnum.DICTIONARY:
                    values = self._get_rule_param(
                        rule.params,
                        "values",
                        "allowed_values",
                        "value",
                    )
                    if values is None:
                        values = []
                    elif not isinstance(values, list):
                        values = [values]
                    condition = f"source_row.{quoted_column}::text <> ALL($1::text[])"
                    params = [[str(value) for value in values]]

                elif rule.rule_type == RuleTypeEnum.RANGE:
                    minimum = self._get_rule_param(rule.params, "min", "minimum")
                    maximum = self._get_rule_param(rule.params, "max", "maximum")
                    if minimum is not None and maximum is not None:
                        condition = (
                            f"source_row.{quoted_column} < $1 "
                            f"OR source_row.{quoted_column} > $2"
                        )
                        params = [minimum, maximum]
                    elif minimum is not None:
                        condition = f"source_row.{quoted_column} < $1"
                        params = [minimum]
                    elif maximum is not None:
                        condition = f"source_row.{quoted_column} > $1"
                        params = [maximum]

                if condition is not None:
                    conditions.append({
                        "rule": rule,
                        "target_columns": [column],
                        "query": f"""
                            SELECT source_row.ctid::text AS row_key,
                                   to_jsonb(source_row) AS row_data
                            FROM {table_name} AS source_row
                            WHERE {condition}
                        """,
                        "params": params,
                    })

        return conditions

    @staticmethod
    def _get_rule_param(params: dict | None, *names: str) -> Any:
        params = params or {}
        for name in names:
            value = params.get(name)
            if value is not None:
                while isinstance(value, dict) and "value" in value:
                    value = value["value"]
                return value

            value = params.get("value")
            while isinstance(value, dict):
                if name in value:
                    value = value[name]
                    while isinstance(value, dict) and "value" in value:
                        value = value["value"]
                    return value
                if "value" not in value:
                    break
                value = value["value"]
        return None

    @staticmethod
    def _get_table_name(schema_name: str | None, table_name: str) -> str:
        quoted_table = RunService._quote_identifier(table_name)
        if schema_name is None:
            return quoted_table

        return f"{RunService._quote_identifier(schema_name)}.{quoted_table}"

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        return '"' + identifier.replace('"', '""') + '"'

    @staticmethod
    def _keep_active_rules(rules: list[RuleReadDTO]) -> list[RuleReadDTO]:
        return [rule for rule in rules if rule.is_active]
