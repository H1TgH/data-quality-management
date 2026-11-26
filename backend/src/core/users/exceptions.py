class UserAlreadyExistsException(Exception):
    """Пользователь уже существует."""


class InvalidCredentialsException(Exception):
    """Некорректные данные для входа."""


class InvalidTokenException(Exception):
    """Некорректный JWT токен."""


class TokenIsMissingException(Exception):
    """JWT токен отсутвует."""


class UserDoesNotExistException(Exception):
    """Пользователь не существует."""
