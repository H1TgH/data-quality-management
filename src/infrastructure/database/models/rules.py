from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime as PGDateTime, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.rules.enums import RuleActionEnum, RuleTypeEnum
from infrastructure.database.database import Base


class RuleModel(Base):
    __tablename__ = "rules"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4())
    )

    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    rule_type: Mapped[RuleTypeEnum] = mapped_column(
        ENUM(RuleTypeEnum, name="rule_type"),
        nullable=False
    )

    target_columns: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False
    )

    params: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb")
    )

    action: Mapped[RuleActionEnum] = mapped_column(
        ENUM(RuleActionEnum, name="rule_action"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        PGDateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        PGDateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
