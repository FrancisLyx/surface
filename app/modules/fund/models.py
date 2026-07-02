from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class UserFavoriteFund(Base):
    __tablename__ = "user_favorite_funds"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "fund_code", name="uq_user_favorite_funds_user_id_fund_code"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fund_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    fund_name: Mapped[str] = mapped_column(String(255), nullable=False)
    fund_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
