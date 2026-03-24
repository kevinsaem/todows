"""
비동기 데이터베이스 설정 모듈

개발 환경에서는 aiosqlite를 사용하고,
프로덕션에서는 PostgreSQL + asyncpg로 전환할 수 있다.
"""

import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# .env에서 DATABASE_URL을 읽거나, 기본값으로 SQLite 사용
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{Path(__file__).parent.parent / 'todos.db'}",
)

# 비동기 엔진 생성
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    # SQLite에서는 check_same_thread=False 필요
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# 비동기 세션 팩토리
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy 선언적 베이스 클래스"""
    pass


async def get_db() -> AsyncSession:
    """FastAPI 의존성 주입용 DB 세션 제공자"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """애플리케이션 시작 시 테이블 생성"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """애플리케이션 종료 시 엔진 정리"""
    await engine.dispose()
