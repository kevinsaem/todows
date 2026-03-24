"""
할일 조회 테스트

테스트 케이스:
- GET /api/todos → 전체 할일 조회
- GET /api/todos/today → 오늘 할일 조회
- 빈 목록일 때 정상 응답
"""

import pytest
from httpx import AsyncClient

from app.models.todo import Todo


@pytest.mark.asyncio
async def test_get_all_todos(async_client: AsyncClient, sample_todo: Todo):
    """전체 할일 조회 시 등록된 할일이 목록에 포함된다."""
    response = await async_client.get("/api/todos")

    assert response.status_code == 200
    data = response.json()
    assert "todos" in data
    assert "count" in data
    assert data["count"] >= 1
    # 샘플 할일이 목록에 있는지 확인
    titles = [t["title"] for t in data["todos"]]
    assert "테스트 할일" in titles


@pytest.mark.asyncio
async def test_get_today_todos(async_client: AsyncClient, sample_todo: Todo):
    """오늘 할일 조회 시 오늘 날짜의 할일만 반환한다."""
    response = await async_client.get("/api/todos/today")

    assert response.status_code == 200
    data = response.json()
    assert "todos" in data
    assert "count" in data
    # sample_todo는 오늘 날짜이므로 포함되어야 한다
    assert data["count"] >= 1


@pytest.mark.asyncio
async def test_get_todos_empty_list(async_client: AsyncClient):
    """할일이 없을 때 빈 목록과 count 0을 반환한다."""
    response = await async_client.get("/api/todos")

    assert response.status_code == 200
    data = response.json()
    assert data["todos"] == []
    assert data["count"] == 0
