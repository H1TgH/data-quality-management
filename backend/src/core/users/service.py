import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import bcrypt
from jose import ExpiredSignatureError, JWTError, jwt

from core.users.entities import CurrentUserDTO, TokensDTO, UserCreationDTO, UserLoginDTO
from core.users.exceptions import (
    InvalidCredentialsException,
    InvalidTokenException,
    TokenIsMissingException,
    UserAlreadyExistsException,
    UserDoesNotExistException,
)
from infrastructure.database.repositories.user import UserRepository
from settings import settings


class UserService:
    def __init__(
        self,
        user_repository: UserRepository
    ) -> None:
        self.user_repo = user_repository

    async def register_user(
        self,
        data: UserCreationDTO,
    ) -> TokensDTO:
        user = await self.user_repo.get_by_email(data.email)
        if user is not None:
            raise UserAlreadyExistsException("Пользователь с таким email уже существует")

        password_hash = await self.hash_password(data.password)
        user_id = await self.user_repo.create_user(
            UserCreationDTO(
                name=data.name,
                email=data.email,
                password=password_hash,
            )
        )
        return self._create_tokens(user_id)

    async def login_user(
        self,
        data: UserLoginDTO,
    ) -> TokensDTO:
        user = await self.user_repo.get_by_email(data.email)
        if user is None or not await self.verify_password(data.password, user.password):
            raise InvalidCredentialsException("Неверный email или пароль")

        return self._create_tokens(str(user.id))

    async def refresh_access_token(self, refresh_token: str | None) -> str:
        user_id = self.get_user_id_from_token_or_raise(refresh_token, "refresh")
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UserDoesNotExistException("Пользователь не найден")

        return self._create_token(
            {"sub": str(user_id), "type": "access"},
            timedelta(minutes=settings.auth.access_ttl),
        )

    async def get_current_user(self, access_token: str | None) -> CurrentUserDTO:
        user_id = self.get_user_id_from_token_or_raise(access_token, "access")
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UserDoesNotExistException("Пользователь не найден")

        return CurrentUserDTO(
            id=str(user.id),
            name=user.name or "",
            email=user.email,
        )

    @staticmethod
    async def hash_password(password: str) -> str:
        password_hash = await asyncio.to_thread(
            bcrypt.hashpw,
            password.encode("utf-8"),
            bcrypt.gensalt(),
        )
        return password_hash.decode("utf-8")

    @staticmethod
    async def verify_password(password: str, password_hash: str | None) -> bool:
        if not password_hash or not password_hash.startswith("$2"):
            return False

        return await asyncio.to_thread(
            bcrypt.checkpw,
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )

    def _create_tokens(self, user_id: str) -> TokensDTO:
        return TokensDTO(
            access_token=self._create_token(
                {"sub": user_id, "type": "access"},
                timedelta(minutes=settings.auth.access_ttl),
            ),
            refresh_token=self._create_token(
                {"sub": user_id, "type": "refresh"},
                timedelta(days=settings.auth.refresh_ttl),
            ),
        )

    @staticmethod
    def _create_token(data: dict[str, Any], expires_delta: timedelta) -> str:
        payload = data.copy()
        payload["exp"] = datetime.now(UTC) + expires_delta
        return jwt.encode(
            payload,
            settings.auth.secret_key.get_secret_value(),
            settings.auth.algorithm,
        )

    @classmethod
    def get_user_id_from_token_or_raise(
        cls,
        token: str | None,
        token_type: str,
    ) -> UUID:
        if not token:
            raise TokenIsMissingException("Токен отсутствует")

        try:
            payload = jwt.decode(
                token,
                settings.auth.secret_key.get_secret_value(),
                algorithms=[settings.auth.algorithm],
            )
        except ExpiredSignatureError as exc:
            raise InvalidTokenException("Срок действия токена истёк") from exc
        except JWTError as exc:
            raise InvalidTokenException("Некорректный токен") from exc

        if payload.get("type") != token_type or not payload.get("sub"):
            raise InvalidTokenException("Некорректный тип токена")

        try:
            return UUID(payload["sub"])
        except ValueError as exc:
            raise InvalidTokenException("Некорректный токен") from exc
