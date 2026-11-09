"""EP5 · Open-Closed 실습: 새 정책은 새 클래스 + 새 테스트 파일로만 추가된다."""

from decimal import Decimal

from shop.discounts import BestOf, FirstOrderOff, NoDiscount, PercentOff, policy_for
from shop.pricing import calculate_total


def test_first_order_gets_3000_off(make_order):
    policy = FirstOrderOff(is_first_order=lambda customer_id: True)
    assert policy.discount_for(make_order(amount="20000")) == Decimal("3000")


def test_returning_customer_gets_no_discount(make_order):
    policy = FirstOrderOff(is_first_order=lambda customer_id: False)
    assert policy.discount_for(make_order(amount="20000")) == Decimal("0")


def test_first_order_check_uses_customer_id(make_order):
    seen: list[str] = []

    def is_first_order(customer_id: str) -> bool:
        seen.append(customer_id)
        return customer_id == "NEW"

    policy = FirstOrderOff(is_first_order)
    assert policy.discount_for(make_order(customer_id="NEW")) == Decimal("3000")
    assert policy.discount_for(make_order(customer_id="OLD")) == Decimal("0")
    assert seen == ["NEW", "OLD"]


def test_best_of_prefers_larger_discount_over_first_order(make_order):
    # 100,000원이면 회원 5%(5,000원)가 첫 주문(3,000원)보다 크다
    policy = BestOf(PercentOff(5), FirstOrderOff(lambda _: True))
    assert policy.discount_for(make_order(amount="100000")) == Decimal("5000")


def test_calculate_total_applies_first_order_discount(make_order):
    # 20,000 - 3,000 = 17,000, 5만원 미만이라 배송비 3,000원 → 20,000
    order = make_order(amount="20000")
    assert calculate_total(order, FirstOrderOff(lambda _: True)) == Decimal("20000")


def test_calculate_total_caps_discount_at_subtotal(make_order):
    # 1,000원짜리 주문에 3,000원 할인 → 0원 + 배송비 3,000원
    order = make_order(amount="1000")
    assert calculate_total(order, FirstOrderOff(lambda _: True)) == Decimal("3000")


# Factory 연결: is_first_order를 넘길 때만 첫 주문 할인이 후보가 된다
def test_factory_applies_first_order_discount(make_order):
    order = make_order(amount="20000", customer_id="NEW")
    policy = policy_for(order, is_first_order=lambda customer_id: customer_id == "NEW")
    assert policy.discount_for(order) == Decimal("3000")


def test_factory_gives_returning_customer_nothing(make_order):
    order = make_order(amount="20000")
    policy = policy_for(order, is_first_order=lambda _: False)
    assert policy.discount_for(order) == Decimal("0")


def test_factory_without_lookup_ignores_first_order(make_order):
    # 기존 호출 방식(policy_for(order))은 그대로 할인 없음
    assert isinstance(policy_for(make_order()), NoDiscount)


def test_factory_picks_best_of_first_order_member_and_coupon(make_order):
    order = make_order(amount="40000", coupon="SAVE5000", member=True)
    # 첫 주문 3,000 · 회원 5% 2,000 · 쿠폰 5,000 → 쿠폰
    assert policy_for(order, is_first_order=lambda _: True).discount_for(order) == Decimal("5000")


def test_factory_first_order_beats_member_discount(make_order):
    order = make_order(amount="20000", member=True)
    # 첫 주문 3,000 > 회원 5% 1,000
    assert policy_for(order, is_first_order=lambda _: True).discount_for(order) == Decimal("3000")
