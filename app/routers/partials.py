"""
HTMX 파셜 라우터 (/partials)

HTMX 요청에 대해 HTML 프래그먼트를 반환한다.
데이터 명세서의 HTMX 파셜 라우트 정의를 따른다.
"""

from datetime import date, time
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.todo import Todo

router = APIRouter(prefix="/partials", tags=["partials"])


# ─── 헬퍼 함수 ───


async def _get_todo_or_404(todo_id: UUID, db: AsyncSession) -> Todo:
    """ID로 할일을 조회하고, 없으면 404 반환"""
    result = await db.execute(select(Todo).where(Todo.id == str(todo_id)))
    todo = result.scalar_one_or_none()
    if todo is None:
        raise HTTPException(status_code=404, detail="할일을 찾을 수 없습니다")
    return todo


async def _get_today_todos(db: AsyncSession) -> list[Todo]:
    """오늘의 할일 목록 조회 (미완료 먼저, 시간순)"""
    today = date.today()
    stmt = (
        select(Todo)
        .where(Todo.scheduled_date == today)
        .order_by(
            Todo.is_completed.asc(),
            case((Todo.scheduled_time.is_(None), 1), else_=0),
            Todo.scheduled_time.asc(),
            Todo.created_at.asc(),
        )
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


def _parse_time_string(time_str: str | None) -> time | None:
    """시간 문자열을 time 객체로 변환 (유효하지 않으면 None)"""
    if not time_str or not time_str.strip():
        return None
    try:
        # "HH:MM" 또는 "HH:MM:SS" 형식 지원
        parts = time_str.strip().split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        second = int(parts[2]) if len(parts) > 2 else 0
        return time(hour, minute, second)
    except (ValueError, IndexError):
        return None


def _parse_date_string(date_str: str | None) -> date:
    """날짜 문자열을 date 객체로 변환 (유효하지 않으면 오늘)"""
    if not date_str or not date_str.strip():
        return date.today()
    try:
        return date.fromisoformat(date_str.strip())
    except ValueError:
        return date.today()


# ─── 엔드포인트 ───


@router.get("/todo-list", response_class=HTMLResponse)
async def get_todo_list_partial(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """할일 목록 HTML 파셜 반환"""
    todos = await _get_today_todos(db)

    # 미완료 / 완료 분리
    incomplete_todos = [t for t in todos if not t.is_completed]
    completed_todos = [t for t in todos if t.is_completed]

    templates = request.app.state.templates
    html = templates.TemplateResponse(
        "partials/todo-list.html",
        {
            "request": request,
            "incomplete_todos": incomplete_todos,
            "completed_todos": completed_todos,
            "total_count": len(todos),
        },
    )
    return html


@router.post("/todos", response_class=HTMLResponse)
async def create_todo_partial(
    request: Request,
    title: str = Form(...),
    description: str | None = Form(None),
    scheduled_date: str | None = Form(None),
    scheduled_time: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """할일 등록 후 목록 HTML 반환"""
    # 제목 유효성 검사
    if not title or not title.strip():
        raise HTTPException(status_code=400, detail="제목은 필수입니다")
    if len(title.strip()) > 200:
        raise HTTPException(status_code=400, detail="제목은 200자까지 입력 가능합니다")

    # 할일 생성
    todo = Todo(
        title=title.strip(),
        description=description.strip() if description else None,
        scheduled_date=_parse_date_string(scheduled_date),
        scheduled_time=_parse_time_string(scheduled_time),
    )
    db.add(todo)
    await db.flush()

    # 오늘 할일 목록 다시 조회하여 반환
    todos = await _get_today_todos(db)
    incomplete_todos = [t for t in todos if not t.is_completed]
    completed_todos = [t for t in todos if t.is_completed]

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "partials/todo-list.html",
        {
            "request": request,
            "incomplete_todos": incomplete_todos,
            "completed_todos": completed_todos,
            "total_count": len(todos),
        },
    )


@router.put("/todos/{todo_id}", response_class=HTMLResponse)
async def update_todo_partial(
    request: Request,
    todo_id: UUID,
    title: str = Form(...),
    description: str | None = Form(None),
    scheduled_date: str | None = Form(None),
    scheduled_time: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """할일 수정 후 해당 항목 HTML 반환"""
    todo = await _get_todo_or_404(todo_id, db)

    # 제목 유효성 검사
    if not title or not title.strip():
        raise HTTPException(status_code=400, detail="제목은 필수입니다")

    todo.title = title.strip()
    todo.description = description.strip() if description else None
    todo.scheduled_date = _parse_date_string(scheduled_date)
    todo.scheduled_time = _parse_time_string(scheduled_time)

    await db.flush()
    await db.refresh(todo)

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "partials/todo-item.html",
        {"request": request, "todo": todo},
    )


@router.delete("/todos/{todo_id}", response_class=HTMLResponse)
async def delete_todo_partial(
    request: Request,
    todo_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """할일 삭제 후 전체 목록 HTML 반환"""
    todo = await _get_todo_or_404(todo_id, db)
    await db.delete(todo)
    await db.flush()

    # 전체 목록 다시 조회하여 반환
    todos = await _get_today_todos(db)
    incomplete_todos = [t for t in todos if not t.is_completed]
    completed_todos = [t for t in todos if t.is_completed]

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "partials/todo-list.html",
        {
            "request": request,
            "incomplete_todos": incomplete_todos,
            "completed_todos": completed_todos,
        },
    )


@router.patch("/todos/{todo_id}/toggle", response_class=HTMLResponse)
async def toggle_todo_partial(
    request: Request,
    todo_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """완료/미완료 토글 후 전체 목록 HTML 반환"""
    todo = await _get_todo_or_404(todo_id, db)
    todo.is_completed = not todo.is_completed

    await db.flush()

    # 전체 목록 다시 조회하여 반환 (프론트엔드가 #todo-list-container innerHTML을 교체함)
    todos = await _get_today_todos(db)
    incomplete_todos = [t for t in todos if not t.is_completed]
    completed_todos = [t for t in todos if t.is_completed]

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "partials/todo-list.html",
        {
            "request": request,
            "incomplete_todos": incomplete_todos,
            "completed_todos": completed_todos,
        },
    )
