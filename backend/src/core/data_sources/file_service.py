import asyncio
import csv
import os
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import uuid4

from core.data_sources.entities import FileSourceDTO
from core.data_sources.exceptions import (
    EmptyFileException,
    FileParsingException,
    FileTooLargeException,
    UnsupportedFileFormatException,
)
from core.data_sources.staging import staging_table_name
from infrastructure.database.repositories.data_source import DataSourceRepository
from infrastructure.database.staging_loader import StagingLoader
from infrastructure.file_parsers.reader import read_table


class FileDataSourceService:
    MAX_FILE_SIZE = 50 * 1024 * 1024
    SUPPORTED_FORMATS = {"csv", "xlsx", "xls"}

    def __init__(
        self,
        data_source_repository: DataSourceRepository,
        staging_loader: StagingLoader,
    ) -> None:
        self.data_source_repo = data_source_repository
        self.staging_loader = staging_loader

    async def upload(
        self,
        filename: str,
        chunks: AsyncIterator[bytes],
    ) -> FileSourceDTO:
        file_name = Path(filename).name
        file_format = Path(file_name).suffix.lower().lstrip(".")

        if file_format not in self.SUPPORTED_FORMATS:
            raise UnsupportedFileFormatException(
                "Поддерживаются только файлы .csv, .xlsx и .xls"
            )

        fd, tmp_path = tempfile.mkstemp(suffix=f".{file_format}")
        os.close(fd)

        try:
            size = await self._save_to_disk(tmp_path, chunks)
            return await self._load_file(tmp_path, file_name, file_format, size)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    async def _save_to_disk(self, path: str, chunks: AsyncIterator[bytes]) -> int:
        size = 0
        with open(path, "wb") as out:
            async for chunk in chunks:
                size += len(chunk)
                if size > self.MAX_FILE_SIZE:
                    raise FileTooLargeException("Размер файла превышает 50 МБ")
                await asyncio.to_thread(out.write, chunk)

        if size == 0:
            raise EmptyFileException("Файл пустой")
        return size

    async def _load_file(
        self,
        path: str,
        file_name: str,
        file_format: str,
        size: int,
    ) -> FileSourceDTO:
        source_id = str(uuid4())
        table_name = staging_table_name(source_id)
        rows = None

        try:
            headers, rows = await asyncio.to_thread(read_table, path, file_format)
            row_count = await self.staging_loader.load(table_name, headers, rows)
        except (UnicodeDecodeError, csv.Error) as exc:
            raise FileParsingException(
                "Не удалось прочитать файл: проверьте кодировку и формат"
            ) from exc
        finally:
            if rows is not None:
                rows.close()   # закрывает открытый csv-файл

        try:
            await self.data_source_repo.create_file(
                source_id=source_id,
                file_name=file_name,
                file_size_bytes=size,
                file_format=file_format,
            )
        except Exception:
            await self.staging_loader.drop(table_name)
            raise

        return FileSourceDTO(
            source_id=source_id,
            file_name=file_name,
            file_size_bytes=size,
            row_count=row_count,
            columns_count=len(headers),
        )
