"""
페이지 라우터 (Jinja2 HTML 렌더링)

메인 페이지 등 풀 HTML 페이지를 반환하는 라우트.
"""

from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.todo import Todo

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """
    메인 페이지 렌더링

    오늘의 할일 목록을 포함하여 index.html을 반환한다.
    """
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
    todos = list(result.scalars().all())

    # 미완료 / 완료 분리
    incomplete_todos = [t for t in todos if not t.is_completed]
    completed_todos = [t for t in todos if t.is_completed]

    # 한국어 날짜 포맷
    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    today_str = f"{today.year}년 {today.month}월 {today.day}일 {weekdays[today.weekday()]}"

    templates = request.app.state.templates
    context = {
        "request": request,
        "today_str": today_str,
        "todo_count": len(todos),
        "incomplete_todos": incomplete_todos,
        "completed_todos": completed_todos,
    }
    return templates.TemplateResponse("index.html", context)
