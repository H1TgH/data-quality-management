from fastapi import APIRouter, Depends, Request, Response, status

from api.auth.decorators import handle_user_exceptions
from api.auth.schemas import CurrentUserSchema, UserLoginSchema, UserRegistrationSchema
from api.dependencies import get_current_user, get_user_service
from core.users.entities import CurrentUserDTO, UserCreationDTO, UserLoginDTO
from core.users.service import UserService
from settings import settings


router = APIRouter(
    prefix="/users/auth",
    tags=["auth"],
)


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        "user_access_token",
        access_token,
        max_age=settings.security.access_ttl * 60,
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        "user_refresh_token",
        refresh_token,
        max_age=settings.security.refresh_ttl * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
    )


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED
)
@handle_user_exceptions
async def register_user(
    data: UserRegistrationSchema,
    response: Response,
    service: UserService = Depends(get_user_service),
):
    tokens = await service.register_user(UserCreationDTO(**data.model_dump()))
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return {"msg": "Пользователь успешно создан"}


@router.post(
    "/login",
    status_code=status.HTTP_200_OK
)
@handle_user_exceptions
async def login_user(
    data: UserLoginSchema,
    response: Response,
    service: UserService = Depends(get_user_service),
):
    tokens = await service.login_user(UserLoginDTO(**data.model_dump()))
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return {"msg": "Вход выполнен"}


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK
)
@handle_user_exceptions
async def refresh_access_token(
    request: Request,
    response: Response,
    service: UserService = Depends(get_user_service),
):
    refresh_token = request.cookies.get("user_refresh_token")
    access_token = await service.refresh_access_token(refresh_token)
    response.set_cookie(
        "user_access_token",
        access_token,
        max_age=settings.security.access_ttl * 60,
        httponly=True,
        samesite="lax",
    )
    return {"msg": "Токен обновлён"}


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK
)
async def logout(response: Response):
    response.delete_cookie("user_access_token")
    response.delete_cookie("user_refresh_token")
    return {"msg": "Выход выполнен"}


@router.get(
    "/me",
    response_model=CurrentUserSchema
)
async def get_me(
    current_user: CurrentUserDTO = Depends(get_current_user),
):
    return current_user
