from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime as PGDateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.core.data_sources.enums import DataSourceTypeEnum
from backend.src.infrastructure.database.database import Base


class DataSourceModel(Base):
    __tablename__ = "data_sources"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4())
    )

    type: Mapped[DataSourceTypeEnum] = mapped_column(
        ENUM(DataSourceTypeEnum, name="data_source_type"),
        nullable=False
    )

    host: Mapped[str | None] = mapped_column(
        String
    )

    port: Mapped[int | None] = mapped_column(
        Integer
    )

    db_name: Mapped[str | None] = mapped_column(
        String
    )

    username: Mapped[str | None] = mapped_column(
        String
    )

    password_encrypted: Mapped[str | None] = mapped_column(
        String
    )

    created_at: Mapped[datetime] = mapped_column(
        PGDateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
