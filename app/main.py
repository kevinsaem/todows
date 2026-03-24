"""
할일 앱 — FastAPI 메인 애플리케이션

모바일 전용 할일 웹앱의 서버 진입점.
Jinja2 템플릿, CORS, 정적 파일, 라우터를 설정한다.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import close_db, init_db
from app.routers import pages, partials, todos
from app.security import setup_security

# ─── 경로 설정 ───

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


# ─── 앱 생명주기 ───


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """앱 시작/종료 시 DB 초기화 및 정리"""
    await init_db()
    yield
    await close_db()


# ─── 앱 생성 ───

app = FastAPI(
    title="할일 앱",
    description="음성 입력으로 할 일을 등록하는 모바일 전용 웹앱",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,      # 프로덕션 보안: Swagger UI 비활성화
    redoc_url=None,     # 프로덕션 보안: ReDoc 비활성화
)

# ─── CORS 설정 ───

import os

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "HX-Request", "HX-Target", "HX-Trigger"],
)

# ─── 보안 미들웨어 ───

setup_security(app)

# ─── Jinja2 템플릿 ───

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
# 다른 라우터에서 접근할 수 있도록 app.state에 저장
app.state.templates = templates

# ─── 정적 파일 ───

# static 디렉토리가 존재하면 마운트
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ─── 라우터 등록 ───

app.include_router(pages.router)
app.include_router(todos.router)
app.include_router(partials.router)


# ─── 글로벌 에러 핸들러 ───


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """404 에러 핸들러"""
    return JSONResponse(
        status_code=404,
        content={"error": "요청한 리소스를 찾을 수 없습니다"},
    )


@app.exception_handler(400)
async def bad_request_handler(request: Request, exc: Exception) -> JSONResponse:
    """400 에러 핸들러"""
    return JSONResponse(
        status_code=400,
        content={"error": str(exc.detail) if hasattr(exc, "detail") else "잘못된 요청입니다"},
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """500 에러 핸들러"""
    return JSONResponse(
        status_code=500,
        content={"error": "서버 오류가 발생했습니다"},
    )
