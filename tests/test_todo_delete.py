"""
할일 삭제 테스트 (DELETE /api/todos/{id})

테스트 케이스:
- 정상 삭제 → 200 + {"ok": true}
- 존재하지 않는 ID로 삭제 → 404
"""

import pytest
from httpx import AsyncClient

from app.models.todo import Todo


@pytest.mark.asyncio
async def test_delete_todo(async_client: AsyncClient, sample_todo: Todo):
    """할일을 삭제하면 200과 ok: true를 반환한다."""
    response = await async_client.delete(f"/api/todos/{sample_todo.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True

    # 삭제 후 조회하면 목록에 없어야 한다
    list_response = await async_client.get("/api/todos")
    todos = list_response.json()["todos"]
    ids = [t["id"] for t in todos]
    assert sample_todo.id not in ids


@pytest.mark.asyncio
async def test_delete_nonexistent_todo(async_client: AsyncClient):
    """존재하지 않는 ID로 삭제하면 404를 반환한다."""
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await async_client.delete(f"/api/todos/{fake_id}")

    assert response.status_code == 404
