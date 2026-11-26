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
        postgres_client: PostgresClient,
        staging_credentials: DataSourceCredsDTO,
    ) -> None:
        self.project_service = project_service
        self.rule_service = rule_service
        self.data_source_service = data_source_service
        self.run_repo = run_repository
        self.error_log_repo = error_log_repository
        self.cleaned_rows_repo = cleaned_rows_repository
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
