from functools import wraps

from fastapi import HTTPException, status

from core.data_sources.exceptions import (
    DataSourceAuthException,
    DataSourceConfigurationException,
    DataSourceNetworkException,
    DataSourceNotFoundException,
    DataSourceTimeoutException,
    DataSourceUnavailableException,
    EmptyFileException,
    FileParsingException,
    FileTooLargeException,
    TooManyRowsException,
    UnsupportedFileFormatException,
)


def handle_data_source_exceptions(func):
    @wraps(func)
    async def wrapped(*args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except DataSourceNetworkException as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

        except DataSourceUnavailableException as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

        except DataSourceTimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=str(exc),
            ) from exc

        except DataSourceAuthException as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        except DataSourceConfigurationException as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        except DataSourceNotFoundException as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc)
            ) from exc

        except (UnsupportedFileFormatException, EmptyFileException, FileParsingException) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc)
            ) from exc

        except (FileTooLargeException, TooManyRowsException) as exc:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=str(exc)
            ) from exc

    return wrapped
