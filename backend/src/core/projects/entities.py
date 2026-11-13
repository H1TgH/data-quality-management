from dataclasses import dataclass


@dataclass
class ProjectCreationDTO:
    data_source_id: str
    schema_name: str
    table_name: str
    name: str | None = None


@dataclass
class ProjectReadDTO:
    id: str
    data_source_id: str
    name: str
    schema_name: str | None
    table_name: str
