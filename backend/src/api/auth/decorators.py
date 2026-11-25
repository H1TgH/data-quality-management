from functools import wraps

from fastapi import HTTPException, status

from core.users.exceptions import (
    InvalidCredentialsException,
    InvalidTokenException,
    TokenIsMissingException,
    UserAlreadyExistsException,
    UserDoesNotExistException,
)


def handle_user_exceptions(func):
    @wraps(func)
    async def wrapped(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except UserAlreadyExistsException as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc
        except (InvalidCredentialsException, InvalidTokenException, TokenIsMissingException) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            ) from exc
        except UserDoesNotExistException as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    return wrapped
