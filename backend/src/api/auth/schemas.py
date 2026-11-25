from pydantic import BaseModel, EmailStr, Field


class UserRegistrationSchema(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(max_length=72)


class CurrentUserSchema(BaseModel):
    id: str
    name: str
    email: EmailStr
