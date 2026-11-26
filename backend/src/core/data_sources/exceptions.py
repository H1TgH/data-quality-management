class DataSourceException(Exception):
    """Базовое исключение для источников данных."""


class DataSourceConnectionException(DataSourceException):
    """Базовое исключение для ошибок подключения."""


class DataSourceNetworkException(DataSourceConnectionException):
    """Сетевое ошибка при подключении."""


class DataSourceUnavailableException(DataSourceConnectionException):
    """База данных недоступна."""


class DataSourceTimeoutException(DataSourceConnectionException):
    """Превышение таймаута при попытке подлючения"""


class DataSourceAuthException(DataSourceException):
    """Ошибка аутентификации при подключении."""


class DataSourceConfigurationException(DataSourceException):
    """Некорректная конфигурация подлключения."""


class DataSourceNotFoundException(DataSourceException):
    """Источник данных не найден."""


class FileDataSourceException(Exception):
    """Базовое исключение ошибок загрузки файла."""


class UnsupportedFileFormatException(FileDataSourceException):
    """Неподдерживаемый формат загружаемого файла."""


class FileTooLargeException(FileDataSourceException):
    """Превышен допустимый размер загружаемого файла."""


class TooManyRowsException(FileDataSourceException):
    """Превышено количество максимального количества строк в файле."""


class EmptyFileException(FileDataSourceException):
    """Загружен пустой файл."""


class FileParsingException(FileDataSourceException):
    """Ошибка при попытки прочитать файл."""
