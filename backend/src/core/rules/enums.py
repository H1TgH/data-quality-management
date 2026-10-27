from enum import StrEnum


class RuleTypeEnum(StrEnum):
    UNIQUENESS = "UNIQUENESS"  # Пропуски (NULL / пустая строка)
    NOT_NULL = "NOT_NULL"  # Полные дубликаты
    REGEX = "REGEX"  # Невалидный формат
    DICTIONARY = "DICTIONARY"  # Значение вне справочника
    RANGE = "RANGE"  # Выбросы
    CUSTOM_SQL = "CUSTOM_SQL"  # Логические ошибки


class RuleActionEnum(StrEnum):
    AUTO_CLEAN = "AUTO_CLEAN"
    INDICATE = "INDICATE"
