"""
Pydantic 스키마 (요청/응답 모델)

데이터 명세서(docs/data-spec.md)의 Pydantic 모델 정의를 따른다.
"""

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ─── 요청 모델 ───


class TodoCreate(BaseModel):
    """할일 등록 요청"""

    title: str = Field(..., min_length=1, max_length=200, description="할일 제목 (필수)")
    description: str | None = Field(None, description="상세 내용 (선택)")
    scheduled_date: date | None = Field(None, description="예정 날짜 (선택, 기본값: 오늘)")
    scheduled_time: time | None = Field(None, description="예정 시간 (선택)")

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str) -> str:
        """제목이 공백만으로 이루어지면 안 된다"""
        if not v.strip():
            raise ValueError("제목은 필수입니다")
        return v.strip()


class TodoUpdate(BaseModel):
    """할일 수정 요청 (부분 업데이트)"""

    title: str | None = Field(None, min_length=1, max_length=200, description="할일 제목")
    description: str | None = Field(None, description="상세 내용")
    scheduled_date: date | None = Field(None, description="예정 날짜")
    scheduled_time: time | None = Field(None, description="예정 시간")

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str | None) -> str | None:
        """제목이 주어지면 공백만으로 이루어지면 안 된다"""
        if v is not None and not v.strip():
            raise ValueError("제목은 비어있을 수 없습니다")
        return v.strip() if v else v


# ─── 응답 모델 ───


class TodoResponse(BaseModel):
    """단일 할일 응답"""

    id: UUID
    title: str
    description: str | None
    scheduled_date: date
    scheduled_time: time | None
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TodoListResponse(BaseModel):
    """할일 목록 응답"""

    todos: list[TodoResponse]
    count: int
