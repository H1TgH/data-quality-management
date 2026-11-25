from dataclasses import dataclass


@dataclass
class UserCreationDTO:
    name: str
    email: str
    password: str


@dataclass
class UserLoginDTO:
    email: str
    password: str


@dataclass
class TokensDTO:
    access_token: str
    refresh_token: str


@dataclass
class CurrentUserDTO:
    id: str
    name: str
    email: str
