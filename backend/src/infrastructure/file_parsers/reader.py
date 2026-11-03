import codecs
import csv
import datetime as dt
from collections.abc import Iterator
from typing import Any

from python_calamine import CalamineWorkbook

from core.data_sources.exceptions import EmptyFileException, FileParsingException


MAX_IDENTIFIER_BYTES = 63
SAMPLE_SIZE = 64 * 1024


def read_table(
    path: str,
    file_format: str,
) -> tuple[list[str], Iterator[list[str | None]]]:
    source = _csv_source(path) if file_format == "csv" else _excel_source(path)
    headers = next(source)
    return headers, source


def _csv_source(path: str) -> Iterator[Any]:
    encoding = _detect_encoding(path)

    with open(path, "r", encoding=encoding, newline="") as file:
        first_line = file.readline()
        file.seek(0)

        delimiter = max(",;\t|", key=first_line.count)
        reader = csv.reader(file, delimiter=delimiter)

        header_row = next(reader, None)
        if header_row is None:
            raise EmptyFileException("Файл пустой")

        headers = _normalize_headers(header_row)
        yield headers
        yield from _iter_rows(reader, len(headers))


def _excel_source(path: str) -> Iterator[Any]:
    try:
        workbook = CalamineWorkbook.from_path(path)
        sheet = workbook.get_sheet_by_index(0)
        rows = iter(sheet.iter_rows())
    except Exception as exc:
        raise FileParsingException("Не удалось прочитать Excel-файл") from exc

    header_row = next(rows, None)
    if header_row is None:
        raise EmptyFileException("Файл пустой")

    headers = _normalize_headers(header_row)
    yield headers
    yield from _iter_rows(rows, len(headers))


def _detect_encoding(path: str) -> str:
    with open(path, "rb") as file:
        sample = file.read(SAMPLE_SIZE)

    decoder = codecs.getincrementaldecoder("utf-8-sig")()
    try:
        decoder.decode(sample, final=False)
    except UnicodeDecodeError:
        return "cp1251"
    return "utf-8-sig"


def _iter_rows(source: Iterator[list], width: int) -> Iterator[list[str | None]]:
    for raw in source:
        row = [_to_text(cell) for cell in raw[:width]]
        row.extend([None] * (width - len(row)))

        if any(cell is not None and cell.strip() for cell in row):
            yield row


def _to_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.replace("\x00", "")
        return value if value != "" else None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else repr(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, dt.datetime):
        if value.time() == dt.time(0):
            return value.date().isoformat()
        return value.isoformat(sep=" ")
    if isinstance(value, dt.date):
        return value.isoformat()
    return str(value)


def _truncate(name: str, limit: int) -> str:
    return name.encode("utf-8")[:limit].decode("utf-8", errors="ignore")


def _normalize_headers(raw: list[Any]) -> list[str]:
    headers: list[str] = []
    used: set[str] = set()

    for position, cell in enumerate(raw, start=1):
        base = (_to_text(cell) or "").strip() or f"column_{position}"
        name = _truncate(base, MAX_IDENTIFIER_BYTES)

        counter = 1
        while name in used:
            counter += 1
            suffix = f"_{counter}"
            name = _truncate(base, MAX_IDENTIFIER_BYTES - len(suffix)) + suffix

        used.add(name)
        headers.append(name)

    return headers
