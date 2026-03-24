"""
Playwright E2E 테스트 설정

- 모바일 뷰포트 (375x812, iPhone 크기)
- FastAPI 서버 자동 시작/종료
- 모바일 설정이 적용된 페이지 픽스처
"""

import subprocess
import time

import pytest


# ─── 서버 시작/종료 픽스처 ───

@pytest.fixture(scope="session")
def server():
    """
    E2E 테스트 세션 동안 FastAPI 서버를 실행한다.
    테스트 완료 후 자동 종료된다.
    """
    # uvicorn으로 테스트 서버 시작 (포트 8999 사용하여 충돌 방지)
    proc = subprocess.Popen(
        [
            "uvicorn",
            "app.main:app",
            "--host", "127.0.0.1",
            "--port", "8999",
            "--log-level", "warning",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # 서버가 준비될 때까지 대기
    time.sleep(2)

    yield proc

    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def base_url(server):
    """테스트 서버의 기본 URL"""
    return "http://127.0.0.1:8999"


# ─── 모바일 뷰포트 설정 ───

MOBILE_VIEWPORT = {
    "width": 375,
    "height": 812,
}

MOBILE_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/16.0 Mobile/15E148 Safari/604.1"
)


@pytest.fixture
def browser_context_args():
    """Playwright 브라우저 컨텍스트에 모바일 설정 적용"""
    return {
        "viewport": MOBILE_VIEWPORT,
        "user_agent": MOBILE_USER_AGENT,
        "has_touch": True,
        "is_mobile": True,
    }


@pytest.fixture
def mobile_page(page, base_url):
    """
    모바일 설정이 적용된 페이지.
    기본 URL로 이동한 상태로 제공된다.
    """
    page.set_viewport_size(MOBILE_VIEWPORT)
    page.goto(base_url)
    yield page
