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
        """Установка соединения с внешней базой."""
        ...

    @abstractmethod
    async def get_tables(self) -> list[DataSourceTablesDTO]:
        """Возвращает список таблиц из подключенной бд."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Закрывает подключение с бд."""
        ...
