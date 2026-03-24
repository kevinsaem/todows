"""
할일 앱 — FastAPI 메인 애플리케이션

모바일 전용 할일 웹앱의 서버 진입점.
Jinja2 템플릿, CORS, 정적 파일, 라우터를 설정한다.
"""

import logging
import os
import traceback
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

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─── 앱 생명주기 ───


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """앱 시작/종료 시 DB 초기화 및 정리"""
    logger.info(f"BASE_DIR: {BASE_DIR}")
    logger.info(f"TEMPLATES_DIR: {TEMPLATES_DIR} (exists: {TEMPLATES_DIR.exists()})")
    logger.info(f"STATIC_DIR: {STATIC_DIR} (exists: {STATIC_DIR.exists()})")
    if TEMPLATES_DIR.exists():
        logger.info(f"템플릿 파일: {list(TEMPLATES_DIR.rglob('*.html'))}")
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

if not TEMPLATES_DIR.exists():
    logger.error(f"템플릿 디렉토리가 존재하지 않습니다: {TEMPLATES_DIR}")
    # CWD 기준으로 시도
    alt_templates = Path.cwd() / "app" / "templates"
    if alt_templates.exists():
        logger.info(f"대체 경로 사용: {alt_templates}")
        TEMPLATES_DIR_FINAL = alt_templates
    else:
        TEMPLATES_DIR_FINAL = TEMPLATES_DIR
else:
    TEMPLATES_DIR_FINAL = TEMPLATES_DIR

templates = Jinja2Templates(directory=str(TEMPLATES_DIR_FINAL))
app.state.templates = templates

# ─── 정적 파일 ───

STATIC_DIR_FINAL = STATIC_DIR
if not STATIC_DIR.exists():
    alt_static = Path.cwd() / "app" / "static"
    if alt_static.exists():
        STATIC_DIR_FINAL = alt_static

if STATIC_DIR_FINAL.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR_FINAL)), name="static")

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
    logging.error(f"500 에러 발생: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"error": "서버 오류가 발생했습니다"},
    )
