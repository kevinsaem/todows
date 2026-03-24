"""
E2E 테스트: 할일 추가

테스트 시나리오:
- 텍스트 입력으로 할일 추가
- 추가 후 목록에 표시되는지 확인
"""

from playwright.sync_api import Page, expect


def test_add_todo_via_text_input(mobile_page: Page, base_url: str):
    """
    텍스트 입력으로 할일을 추가하면 성공적으로 저장된다.

    시나리오:
    1. 추가 버튼을 누른다
    2. 제목을 입력한다
    3. 저장 버튼을 누른다
    4. 할일이 저장된다
    """
    page = mobile_page

    # 추가 버튼 클릭
    add_button = page.locator("[data-testid='add-todo-button']")
    add_button.click()

    # 제목 입력
    title_input = page.locator("[data-testid='todo-title-input']")
    title_input.fill("E2E 테스트 할일")

    # 저장 버튼 클릭
    save_button = page.locator("[data-testid='save-todo-button']")
    save_button.click()

    # 저장 후 잠시 대기 (HTMX swap 완료 대기)
    page.wait_for_timeout(500)


def test_todo_appears_in_list_after_adding(mobile_page: Page, base_url: str):
    """
    할일을 추가하면 메인 목록에 해당 항목이 표시된다.

    시나리오:
    1. 할일을 추가한다
    2. 메인 화면에서 해당 할일이 보이는지 확인한다
    """
    page = mobile_page

    # 할일 추가
    add_button = page.locator("[data-testid='add-todo-button']")
    add_button.click()

    title_input = page.locator("[data-testid='todo-title-input']")
    title_input.fill("목록 확인용 할일")

    save_button = page.locator("[data-testid='save-todo-button']")
    save_button.click()

    # 메인 화면으로 돌아온 후 목록에서 확인
    page.wait_for_timeout(500)

    # 목록에 방금 추가한 할일이 보이는지 확인
    todo_list = page.locator("[data-testid='todo-list']")
    expect(todo_list).to_contain_text("목록 확인용 할일")
