from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    exp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    progresses: Mapped[list["UserStepProgress"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class VerificationCode(Base):
    """
    メール送信で使う6桁コード。5分有効・最大3回試行。
    email 単位に最新レコードを使う想定（用途により user_id にしてもよい）。
    """
    __tablename__ = "verification_codes"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts_left: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("email", "created_at", name="uq_email_created_at"),)

class Topic(Base):
    __tablename__ = "topics"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(2048), nullable=True)
    steps: Mapped[list["Step"]] = relationship(back_populates="topic", cascade="all, delete-orphan")

class Step(Base):
    __tablename__ = "steps"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    order_no: Mapped[int] = mapped_column(Integer, nullable=False)  # 1,2,3...
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    topic: Mapped["Topic"] = relationship(back_populates="steps")

class UserStepProgress(Base):
    __tablename__ = "user_step_progress"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    step_id: Mapped[int] = mapped_column(ForeignKey("steps.id", ondelete="CASCADE"), index=True)
    is_cleared: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cleared_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="progresses")
