"""
Todo SQLAlchemy 모델

데이터 명세서(docs/data-spec.md)의 todos 테이블 정의를 따른다.
"""

import uuid
from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Todo(Base):
    """할일 테이블 모델"""

    __tablename__ = "todos"

    # 고유 식별자 (UUID)
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # 할일 제목 (필수, 최대 200자)
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    # 상세 내용 (선택)
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    # 예정 날짜 (필수, 기본값: 오늘)
    scheduled_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )

    # 예정 시간 (선택)
    scheduled_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
        default=None,
    )

    # 완료 여부 (기본값: False)
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # 생성 시각
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    # 수정 시각
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def __repr__(self) -> str:
        return f"<Todo(id={self.id}, title={self.title!r}, completed={self.is_completed})>"
