"""EP6 · Characterization test (golden master).

레거시 코드의 '올바른' 동작은 아무도 모른다. 그래서 '지금의' 동작을 그대로 기록한다.
1단계: 레거시 출력을 스냅샷으로 고정한다.
2단계: 리팩터링한 코드가 수백 가지 입력에서 레거시와 똑같이 출력하는지 비교한다.
"""

import itertools

import pytest

from shop.invoice import CouponType, Line, make_invoice
from shop.legacy.invoice import make_invoice as legacy_make_invoice

# 1단계 · 레거시 출력 스냅샷. 처음엔 비워 두고 실제 출력을 붙여 넣는다.
LEGACY_SNAPSHOT = """\
INVOICE for kim
  Refactoring x1 = 38000
  Clean Code x2 = 66000
  discount: -10400
  shipping: 0
TOTAL: 93600
points earned: 936"""


def test_legacy_snapshot():
    items = [("Refactoring", 38000, 1), ("Clean Code", 33000, 2), ("Free Sticker", 0, 0)]
    assert legacy_make_invoice("kim", items, 1, True) == LEGACY_SNAPSHOT


# 2단계 · 입력 조합을 넓게 만든다. 경계값(29,999 / 30,000 / 50,000 근처)을 일부러 넣는다.
# 47000은 Pen(3,000원)과 합쳐 정확히 50,000원이 되는 값이다.
# 이 값이 없으면 배송비 경계 버그(>= 를 > 로 바꾸는 실수)를 놓친다.
PRICES = [0, 9900, 15000, 29999, 30000, 33000, 47000, 49999, 52631, 100000, 600000]
QUANTITIES = [-1, 0, 1, 2]
COUPONS = [0, 1, 2]
MEMBERSHIP = [False, True]

CASES = list(itertools.product(PRICES, QUANTITIES, COUPONS, MEMBERSHIP))


@pytest.mark.parametrize(("price", "quantity", "coupon", "member"), CASES)
def test_refactored_matches_legacy(price, quantity, coupon, member):
    legacy_items = [("Book", price, quantity), ("Pen", 1500, 2)]
    new_lines = [Line("Book", price, quantity), Line("Pen", 1500, 2)]

    expected = legacy_make_invoice("lee", legacy_items, coupon, member)
    actual = make_invoice("lee", new_lines, CouponType(coupon), member)

    assert actual == expected
