"""
E2E 테스트: 할일 삭제

테스트 시나리오:
- 할일을 삭제하고 목록에서 사라지는지 확인
"""

import uuid

from playwright.sync_api import Page, expect


def test_delete_todo_and_verify_removal(mobile_page: Page, base_url: str):
    """
    할일을 삭제하면 목록에서 사라진다.

    시나리오:
    1. 고유한 이름으로 할일을 추가한다
    2. 해당 할일을 탭하여 수정 모달을 연다
    3. 삭제 버튼을 누른다
    4. 확인 팝업에서 확인을 누른다
    5. 메인 화면에서 해당 할일이 사라졌는지 확인한다
    """
    page = mobile_page
    unique_title = f"삭제테스트_{uuid.uuid4().hex[:8]}"

    # 확인 다이얼로그 처리 (브라우저 confirm) - 먼저 등록
    page.on("dialog", lambda dialog: dialog.accept())

    # 할일 추가
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

    # 목록에 존재하는지 확인
    todo_list = page.locator("[data-testid='todo-list']")
    expect(todo_list).to_contain_text(unique_title)

    # 할일 항목의 편집 영역 클릭하여 수정 모달 열기
    todo_item = page.locator("[data-testid='todo-item']", has_text=unique_title)
    edit_area = todo_item.locator(".cursor-pointer")
    edit_area.click()
    page.wait_for_timeout(500)

    # 삭제 버튼이 보이는지 확인 (editingId가 설정되어야 보임)
    delete_button = page.locator("[data-testid='delete-todo-button']")
    delete_button.wait_for(state="visible", timeout=3000)
    delete_button.click()
    page.wait_for_timeout(1000)

    # 메인 화면에서 해당 할일이 사라졌는지 확인
    page.goto(base_url)
    page.wait_for_timeout(500)

    expect(page.locator("[data-testid='todo-list']")).not_to_contain_text(unique_title)
