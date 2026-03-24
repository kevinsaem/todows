"""
E2E 테스트: 할일 완료 체크

테스트 시나리오:
- 체크박스를 클릭하여 할일 완료/미완료 토글
"""

import re
import uuid

from playwright.sync_api import Page, expect


def test_toggle_todo_complete(mobile_page: Page, base_url: str):
    """
    할일의 체크박스를 클릭하면 완료 상태가 토글된다.

    시나리오:
    1. 할일을 하나 추가한다
    2. 체크박스를 클릭한다
    3. 완료 상태로 변경되는지 확인
    4. 다시 체크박스를 클릭한다
    5. 미완료 상태로 돌아오는지 확인
    """
    page = mobile_page
    unique_title = f"토글테스트_{uuid.uuid4().hex[:8]}"

    # 먼저 할일 추가
    add_button = page.locator("[data-testid='add-todo-button']")
    add_button.click()

    title_input = page.locator("[data-testid='todo-title-input']")
    title_input.fill(unique_title)

    save_button = page.locator("[data-testid='save-todo-button']")
    save_button.click()
    page.wait_for_timeout(1000)

    # 페이지 새로고침으로 모달 닫기
    page.goto(base_url)
    page.wait_for_timeout(500)

    # 해당 할일의 todo-item을 찾는다
    todo_item = page.locator("[data-testid='todo-item']", has_text=unique_title)
    expect(todo_item).to_be_visible()

    # 미완료 상태 확인 (completed 클래스가 없음)
    expect(todo_item).not_to_have_class(re.compile(r"completed"))

    # 해당 항목의 체크박스 클릭 → 완료 처리
    checkbox = todo_item.locator("[data-testid='todo-checkbox']")
    checkbox.click()
    page.wait_for_timeout(1000)

    # HTMX가 전체 목록을 교체하므로 locator를 다시 찾는다
    todo_item = page.locator("[data-testid='todo-item']", has_text=unique_title)
    expect(todo_item).to_have_class(re.compile(r"completed"))

    # 다시 체크박스 클릭 → 미완료 처리
    checkbox = todo_item.locator("[data-testid='todo-checkbox']")
    checkbox.click()
    page.wait_for_timeout(1000)

    # 미완료 상태 확인
    todo_item = page.locator("[data-testid='todo-item']", has_text=unique_title)
    expect(todo_item).not_to_have_class(re.compile(r"completed"))
