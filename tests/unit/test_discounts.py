"""EP5 · Strategy·Factory 덕분에 규칙 하나하나를 따로 테스트할 수 있다."""

from decimal import Decimal

import pytest

from shop.discounts import (
    BestOf,
    FixedAmountOff,
    NoDiscount,
    PercentOff,
    policy_for,
)


def test_fixed_amount_requires_minimum_order(make_order):
    policy = FixedAmountOff(Decimal("5000"), minimum_order=Decimal("30000"))
    assert policy.discount_for(make_order(amount="29999")) == Decimal("0")
    assert policy.discount_for(make_order(amount="30000")) == Decimal("5000")


def test_best_of_picks_larger_discount(make_order):
    policy = BestOf(PercentOff(5), FixedAmountOff(Decimal("5000")))
    # 200,000원이면 5%(10,000원)가 정액(5,000원)보다 크다
    assert policy.discount_for(make_order(amount="200000")) == Decimal("10000")


@pytest.mark.parametrize("percent", [0, 101])
def test_percent_off_rejects_invalid_rate(percent):
    with pytest.raises(ValueError):
        PercentOff(percent)


def test_factory_returns_no_discount_for_plain_order(make_order):
    assert isinstance(policy_for(make_order()), NoDiscount)


def test_factory_combines_member_and_coupon(make_order):
    order = make_order(amount="40000", coupon="SAVE5000", member=True)
    # 회원 5% = 2,000원, 쿠폰 = 5,000원 → 더 큰 쪽
    assert policy_for(order).discount_for(order) == Decimal("5000")


def test_factory_rejects_unknown_coupon(make_order):
    with pytest.raises(ValueError, match="unknown coupon"):
        policy_for(make_order(coupon="NOPE"))


# Open-Closed: 새 정책은 기존 코드를 고치지 않고 클래스 하나로 추가된다
class BuyNGetOne:
    def __init__(self, n: int) -> None:
        self.n = n

    def discount_for(self, order) -> Decimal:
        item = order.items[0]
        free = item.quantity // (self.n + 1)
        return item.unit_price * free


def test_new_policy_plugs_in_without_changes(make_order):
    order = make_order(amount="10000", quantity=3)
    assert BuyNGetOne(2).discount_for(order) == Decimal("10000")
