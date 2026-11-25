from uuid import UUID, uuid4

from sqlalchemy import Row, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.users.entities import UserCreationDTO


class UserRepository:
    def __init__(
        self,
        session: AsyncSession
    ):
        self.session = session

    async def create_user(
        self,
        data: UserCreationDTO
    ) -> str:
        id = uuid4()
        query = text("""
            INSERT INTO users (id, name, password, email)
            VALUES (:id, :name, :password, :email)
            RETURNING id
        """)

        result = await self.session.execute(
            query,
            {
                "id": id,
                "name": data.name,
                "password": data.password,
                "email": data.email
            }
        )
        return str(result.scalar_one())

    async def get_by_email(self, email: str) -> Row | None:
        result = await self.session.execute(
            text("""
                SELECT id, name, email, password
                FROM users
                WHERE email = :email
            """),
            {"email": email},
        )
        return result.one_or_none()

    async def get_by_id(self, user_id: UUID) -> Row | None:
        result = await self.session.execute(
            text("""
                SELECT id, name, email, password
                FROM users
                WHERE id = :user_id
            """),
            {"user_id": user_id},
        )
        return result.one_or_none()
