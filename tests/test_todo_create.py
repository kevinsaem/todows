"""
할일 등록 테스트 (POST /api/todos)

테스트 케이스:
- 모든 필드를 포함한 정상 등록
- 제목만으로 최소 등록
- 빈 제목 → 422 Validation Error
- 200자 초과 제목 → 422 Validation Error
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_todo_with_all_fields(async_client: AsyncClient):
    """모든 필드를 포함하여 할일을 등록하면 201을 반환한다."""
    payload = {
        "title": "피자집 가기",
        "description": "원준이랑 같이",
        "scheduled_date": "2026-03-24",
        "scheduled_time": "10:00:00",
    }

    response = await async_client.post("/api/todos", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "피자집 가기"
    assert data["description"] == "원준이랑 같이"
    assert data["scheduled_date"] == "2026-03-24"
    assert data["scheduled_time"] == "10:00:00"
    assert data["is_completed"] is False
    # id, created_at, updated_at이 자동 생성되어야 한다
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_todo_with_only_title(async_client: AsyncClient):
    """제목만으로 할일을 등록하면 201을 반환한다 (최소 필드)."""
    payload = {
        "title": "장보기",
    }

    response = await async_client.post("/api/todos", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "장보기"
    assert data["description"] is None
    assert data["scheduled_time"] is None
    assert data["is_completed"] is False
    # scheduled_date는 기본값으로 오늘 날짜가 들어간다
    assert data["scheduled_date"] is not None


@pytest.mark.asyncio
async def test_create_todo_with_empty_title(async_client: AsyncClient):
    """빈 제목으로 등록하면 422 Validation Error를 반환한다."""
    payload = {
        "title": "",
    }

    response = await async_client.post("/api/todos", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_todo_with_whitespace_title(async_client: AsyncClient):
    """공백만 있는 제목으로 등록하면 422를 반환한다."""
    payload = {
        "title": "   ",
    }

    response = await async_client.post("/api/todos", json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_todo_with_title_exceeding_200_chars(async_client: AsyncClient):
    """200자 초과 제목으로 등록하면 422 Validation Error를 반환한다."""
    payload = {
        "title": "가" * 201,
    }

    response = await async_client.post("/api/todos", json=payload)

    assert response.status_code == 422
