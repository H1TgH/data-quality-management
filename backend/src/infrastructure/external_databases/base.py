from abc import ABC, abstractmethod

from core.data_sources.entities import DataSourceTablesDTO


class BaseExternalDBClient(ABC):
    @abstractmethod
    async def connect(
        self,
        host: str,
        port: int,
        db_name: str,
        user: str,
        password: str,
        timeout: int,
    ) -> None:
        """Establish connection to external database."""
        ...

    @abstractmethod
    async def get_tables(self) -> list[DataSourceTablesDTO]:
        """Return a list of tables from the connected database."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close database connection."""
        ...
