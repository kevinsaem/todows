"""
보안 유틸리티 모듈
- 입력값 정제(sanitization)
- Rate limiting 설정
- 보안 헤더 미들웨어
"""

import re
import time
from collections import defaultdict
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


# ---------------------------------------------------------------------------
# 1. 입력값 정제 (Input Sanitization)
# ---------------------------------------------------------------------------

def strip_html_tags(text: str) -> str:
    """HTML 태그를 제거하여 XSS 공격을 방지한다.

    Args:
        text: 사용자로부터 받은 원본 텍스트

    Returns:
        HTML 태그가 제거된 안전한 텍스트
    """
    clean = re.sub(r"<[^>]+>", "", text)
    return clean.strip()


def sanitize_input(text: str, max_length: int = 500) -> str:
    """사용자 입력을 정제한다.

    HTML 태그 제거 + 길이 제한을 적용한다.

    Args:
        text: 사용자로부터 받은 원본 텍스트
        max_length: 허용 최대 글자 수 (기본 500자)

    Returns:
        정제된 텍스트
    """
    text = strip_html_tags(text)
    return text[:max_length]


# ---------------------------------------------------------------------------
# 2. Rate Limiting (기본 구현)
# ---------------------------------------------------------------------------

class RateLimiter:
    """IP 기반 요청 횟수 제한.

    설정된 시간 창(window) 내에 최대 요청 수(max_requests)를 초과하면
    429 Too Many Requests를 반환한다.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # {ip: [timestamp, ...]}
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        """해당 IP의 요청이 허용되는지 확인한다."""
        now = time.time()
        window_start = now - self.window_seconds

        # 만료된 기록 제거
        self._requests[client_ip] = [
            ts for ts in self._requests[client_ip] if ts > window_start
        ]

        if len(self._requests[client_ip]) >= self.max_requests:
            return False

        self._requests[client_ip].append(now)
        return True


# 기본 Rate Limiter 인스턴스 (분당 60회)
rate_limiter = RateLimiter(max_requests=60, window_seconds=60)


# ---------------------------------------------------------------------------
# 3. 보안 헤더 미들웨어
# ---------------------------------------------------------------------------

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """응답에 보안 관련 HTTP 헤더를 추가하는 미들웨어."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)

        # MIME 타입 스니핑 방지
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 클릭재킹 방지 (iframe 삽입 차단)
        response.headers["X-Frame-Options"] = "DENY"

        # XSS 필터 활성화 (레거시 브라우저용)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HTTPS가 아닌 리소스 로드 차단
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdn.tailwindcss.com https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )

        # Referrer 정보 최소화
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 브라우저 기능 제한 (마이크는 음성 입력에 필요하므로 self 허용)
        response.headers["Permissions-Policy"] = (
            "camera=(), geolocation=(), microphone=(self)"
        )

        return response


def setup_security(app: FastAPI) -> None:
    """FastAPI 앱에 보안 미들웨어를 등록한다.

    사용법:
        from app.security import setup_security
        app = FastAPI()
        setup_security(app)
    """
    app.add_middleware(SecurityHeadersMiddleware)
