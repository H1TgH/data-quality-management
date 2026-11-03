class DataSourceException(Exception):
    """Base exception for data source exceptions."""


class DataSourceConnectionException(DataSourceException):
    """Base exception for connection exceptions."""


class DataSourceNetworkException(DataSourceConnectionException):
    """Network-related connection exception."""


class DataSourceUnavailableException(DataSourceConnectionException):
    """Database server is temporarily unavailable."""


class DataSourceTimeoutException(DataSourceConnectionException):
    """Connection attempt timed out."""


class DataSourceAuthException(DataSourceException):
    """Authentication failed."""


class DataSourceConfigurationException(DataSourceException):
    """Invalid database configuration."""


class DataSourceNotFoundException(DataSourceException):
    """Data source not found."""


class FileDataSourceException(Exception):
    """Базовый класс ошибок загрузки файла."""


class UnsupportedFileFormatException(FileDataSourceException):
    pass


class FileTooLargeException(FileDataSourceException):
    pass


class TooManyRowsException(FileDataSourceException):
    pass


class EmptyFileException(FileDataSourceException):
    pass


class FileParsingException(FileDataSourceException):
    pass