"""
할일 수정 테스트 (PUT /api/todos/{id})

테스트 케이스:
- 제목 수정 → 200 + 변경된 제목
- 시간 수정 → 200 + 변경된 시간
- 존재하지 않는 ID로 수정 → 404
"""

import pytest
from httpx import AsyncClient

from app.models.todo import Todo


@pytest.mark.asyncio
async def test_update_todo_title(async_client: AsyncClient, sample_todo: Todo):
    """할일 제목을 수정하면 200과 변경된 데이터를 반환한다."""
    payload = {
        "title": "수정된 할일 제목",
    }

    response = await async_client.put(f"/api/todos/{sample_todo.id}", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "수정된 할일 제목"
    # 나머지 필드는 기존 값 유지
    assert data["description"] == "테스트 설명입니다"
    assert data["id"] == sample_todo.id


@pytest.mark.asyncio
async def test_update_todo_time(async_client: AsyncClient, sample_todo: Todo):
    """할일 예정 시간을 수정하면 200과 변경된 시간을 반환한다."""
    payload = {
        "scheduled_time": "14:30:00",
    }

    response = await async_client.put(f"/api/todos/{sample_todo.id}", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["scheduled_time"] == "14:30:00"


@pytest.mark.asyncio
async def test_update_nonexistent_todo(async_client: AsyncClient):
    """존재하지 않는 ID로 수정하면 404를 반환한다."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    payload = {
        "title": "없는 할일",
    }

    response = await async_client.put(f"/api/todos/{fake_id}", json=payload)

    assert response.status_code == 404
