"""
테스트 공통 설정

- 인메모리 SQLite를 사용하여 테스트 격리
- FastAPI TestClient (httpx AsyncClient)
- 공통 픽스처: async_client, test_db, sample_todo
"""

import asyncio
from datetime import date, time

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.models.todo import Todo

# ─── 테스트용 인메모리 SQLite 엔진 ───

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

test_async_session = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ─── 이벤트 루프 설정 ───

@pytest.fixture(scope="session")
def event_loop():
    """세션 전체에서 하나의 이벤트 루프 사용"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ─── DB 픽스처 ───

@pytest_asyncio.fixture
async def test_db():
    """
    각 테스트마다 깨끗한 DB를 제공한다.
    테이블 생성 → 테스트 실행 → 테이블 삭제
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_async_session() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ─── 의존성 오버라이드용 DB 세션 제공자 ───

async def override_get_db():
    """테스트용 DB 세션을 FastAPI 의존성으로 주입"""
    async with test_async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ─── AsyncClient 픽스처 ───

@pytest_asyncio.fixture
async def async_client(test_db):
    """
    FastAPI 앱에 연결된 httpx AsyncClient를 제공한다.
    DB 의존성을 테스트용으로 오버라이드한다.
    """
    from app.main import app

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# ─── 샘플 데이터 픽스처 ───

@pytest_asyncio.fixture
async def sample_todo(test_db: AsyncSession) -> Todo:
    """
    테스트용 샘플 할일 1개를 DB에 삽입하고 반환한다.
    """
    todo = Todo(
        title="테스트 할일",
        description="테스트 설명입니다",
        scheduled_date=date.today(),
        scheduled_time=time(10, 0),
        is_completed=False,
    )
    test_db.add(todo)
    await test_db.commit()
    await test_db.refresh(todo)
    return todo
