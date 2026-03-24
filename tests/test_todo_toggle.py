"""
완료 토글 테스트 (PATCH /api/todos/{id}/toggle)

테스트 케이스:
- 미완료 → 완료 토글
- 완료 → 미완료 토글
- 존재하지 않는 ID로 토글 → 404
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.todo import Todo


@pytest.mark.asyncio
async def test_toggle_incomplete_to_complete(async_client: AsyncClient, sample_todo: Todo):
    """미완료 할일을 토글하면 is_completed가 True가 된다."""
    # sample_todo는 is_completed=False 상태
    assert sample_todo.is_completed is False

    response = await async_client.patch(f"/api/todos/{sample_todo.id}/toggle")

    assert response.status_code == 200
    data = response.json()
    assert data["is_completed"] is True


@pytest.mark.asyncio
async def test_toggle_complete_to_incomplete(
    async_client: AsyncClient, sample_todo: Todo, test_db: AsyncSession
):
    """완료 상태의 할일을 토글하면 is_completed가 False가 된다."""
    # 먼저 완료 상태로 만든다
    sample_todo.is_completed = True
    test_db.add(sample_todo)
    await test_db.commit()

    response = await async_client.patch(f"/api/todos/{sample_todo.id}/toggle")

    assert response.status_code == 200
    data = response.json()
    assert data["is_completed"] is False


@pytest.mark.asyncio
async def test_toggle_nonexistent_todo(async_client: AsyncClient):
    """존재하지 않는 ID로 토글하면 404를 반환한다."""
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await async_client.patch(f"/api/todos/{fake_id}/toggle")

    assert response.status_code == 404
