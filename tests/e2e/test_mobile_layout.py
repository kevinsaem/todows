"""
E2E 테스트: 모바일 레이아웃

테스트 시나리오:
- 375px 뷰포트에서 레이아웃이 올바르게 렌더링되는지
- 터치 가능 요소가 최소 44px 이상인지
"""

from playwright.sync_api import Page


def test_viewport_renders_correctly_at_375px(mobile_page: Page):
    """
    375px 너비의 모바일 뷰포트에서 페이지가 정상 렌더링된다.

    검증 항목:
    - 가로 스크롤이 발생하지 않는다 (콘텐츠가 뷰포트 안에 있다)
    - 주요 UI 요소가 보인다
    """
    page = mobile_page

    # 뷰포트 크기 확인
    viewport = page.viewport_size
    assert viewport["width"] == 375

    # 가로 스크롤 없는지 확인 (body의 scrollWidth가 뷰포트를 초과하지 않아야 한다)
    scroll_width = page.evaluate("document.body.scrollWidth")
    assert scroll_width <= 375, (
        f"가로 스크롤 발생: body scrollWidth={scroll_width}px > 뷰포트 375px"
    )

    # 주요 요소가 화면에 보이는지 확인
    # 추가 버튼이 뷰포트 안에 있는지
    add_button = page.locator("[data-testid='add-todo-button']")
    if add_button.count() > 0:
        box = add_button.bounding_box()
        assert box is not None, "추가 버튼이 화면에 보이지 않습니다"
        assert box["x"] >= 0 and box["x"] + box["width"] <= 375, (
            "추가 버튼이 뷰포트를 벗어났습니다"
        )


def test_touch_targets_minimum_44px(mobile_page: Page):
    """
    모든 터치 가능 요소(버튼, 체크박스)가 최소 44px x 44px 이상이어야 한다.

    Apple HIG와 WCAG 기준에 따라 모바일 터치 영역은
    최소 44x44px을 확보해야 한다.
    """
    page = mobile_page

    # 모든 클릭 가능 요소를 찾는다 (button, a, input[type=checkbox], [role=button])
    touchable_selectors = [
        "button",
        "a",
        "input[type='checkbox']",
        "[role='button']",
    ]

    min_touch_size = 44

    for selector in touchable_selectors:
        elements = page.locator(selector)
        count = elements.count()

        for i in range(count):
            element = elements.nth(i)

            # 보이는 요소만 검사
            if not element.is_visible():
                continue

            box = element.bounding_box()
            if box is None:
                continue

            assert box["width"] >= min_touch_size, (
                f"{selector} 요소 #{i}의 너비가 {box['width']}px로 "
                f"최소 터치 영역 {min_touch_size}px보다 작습니다"
            )
            assert box["height"] >= min_touch_size, (
                f"{selector} 요소 #{i}의 높이가 {box['height']}px로 "
                f"최소 터치 영역 {min_touch_size}px보다 작습니다"
            )
