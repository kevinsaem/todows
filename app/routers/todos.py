"""
JSON API 라우터 (/api/todos)

데이터 명세서의 API 엔드포인트 정의를 따른다.
프론트엔드에서 fetch()나 다른 클라이언트가 사용하는 순수 JSON API.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.todo import Todo
from app.schemas import TodoCreate, TodoListResponse, TodoResponse, TodoUpdate

router = APIRouter(prefix="/api/todos", tags=["todos"])


# ─── 헬퍼 함수 ───


async def _get_todo_or_404(todo_id: UUID, db: AsyncSession) -> Todo:
    """ID로 할일을 조회하고, 없으면 404 반환"""
    result = await db.execute(select(Todo).where(Todo.id == str(todo_id)))
    todo = result.scalar_one_or_none()
    if todo is None:
        raise HTTPException(status_code=404, detail="할일을 찾을 수 없습니다")
    return todo


# ─── 엔드포인트 ───


@router.get("", response_model=TodoListResponse)
async def get_todos(
    date_filter: date | None = Query(None, alias="date", description="날짜 필터 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
) -> TodoListResponse:
    """
    전체 할일 조회

    date 쿼리 파라미터가 주어지면 해당 날짜의 할일만 반환한다.
    미완료 항목은 시간순 정렬, 완료 항목은 뒤에 표시한다.
    """
    stmt = select(Todo)

    if date_filter is not None:
        stmt = stmt.where(Todo.scheduled_date == date_filter)

    # 미완료 먼저, 그 안에서 시간순 정렬 (NULL은 맨 뒤)
    stmt = stmt.order_by(
        Todo.is_completed.asc(),
        Todo.scheduled_time.asc().nullslast(),
        Todo.created_at.asc(),
    )

    result = await db.execute(stmt)
    todos = result.scalars().all()

    return TodoListResponse(
        todos=[TodoResponse.model_validate(t) for t in todos],
        count=len(todos),
    )


@router.get("/today", response_model=TodoListResponse)
async def get_today_todos(
    db: AsyncSession = Depends(get_db),
) -> TodoListResponse:
    """오늘 할일 조회"""
    today = date.today()
    stmt = (
        select(Todo)
        .where(Todo.scheduled_date == today)
        .order_by(
            Todo.is_completed.asc(),
            Todo.scheduled_time.asc().nullslast(),
            Todo.created_at.asc(),
        )
    )

    result = await db.execute(stmt)
    todos = result.scalars().all()

    return TodoListResponse(
        todos=[TodoResponse.model_validate(t) for t in todos],
        count=len(todos),
    )


@router.post("", response_model=TodoResponse, status_code=201)
async def create_todo(
    body: TodoCreate,
    db: AsyncSession = Depends(get_db),
) -> TodoResponse:
    """할일 등록"""
    todo = Todo(
        title=body.title,
        description=body.description,
        scheduled_date=body.scheduled_date if body.scheduled_date else date.today(),
        scheduled_time=body.scheduled_time,
    )
    db.add(todo)
    await db.flush()
    await db.refresh(todo)

    return TodoResponse.model_validate(todo)


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: UUID,
    body: TodoUpdate,
    db: AsyncSession = Depends(get_db),
) -> TodoResponse:
    """할일 수정 (부분 업데이트)"""
    todo = await _get_todo_or_404(todo_id, db)

    # 전달된 필드만 업데이트
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(todo, field, value)

    await db.flush()
    await db.refresh(todo)

    return TodoResponse.model_validate(todo)


@router.delete("/{todo_id}")
async def delete_todo(
    todo_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """할일 삭제"""
    todo = await _get_todo_or_404(todo_id, db)
    await db.delete(todo)
    await db.flush()

    return {"ok": True}


@router.patch("/{todo_id}/toggle", response_model=TodoResponse)
async def toggle_todo(
    todo_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> TodoResponse:
    """완료/미완료 토글"""
    todo = await _get_todo_or_404(todo_id, db)
    todo.is_completed = not todo.is_completed

    await db.flush()
    await db.refresh(todo)

    return TodoResponse.model_validate(todo)
