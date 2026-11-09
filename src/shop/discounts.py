"""EP5 · Strategy + Factory. 할인 규칙을 if 문이 아니라 객체로 갈아 끼운다."""

from collections.abc import Callable
from decimal import Decimal
from typing import Protocol

from shop.models import Order


class DiscountPolicy(Protocol):
    def discount_for(self, order: Order) -> Decimal: ...


class NoDiscount:
    def discount_for(self, order: Order) -> Decimal:
        return Decimal("0")


class PercentOff:
    def __init__(self, percent: int) -> None:
        if not 0 < percent <= 100:
            raise ValueError("percent must be between 1 and 100")
        self.percent = percent

    def discount_for(self, order: Order) -> Decimal:
        return order.subtotal * Decimal(self.percent) / Decimal(100)


class FixedAmountOff:
    def __init__(self, amount: Decimal, minimum_order: Decimal = Decimal("0")) -> None:
        self.amount = amount
        self.minimum_order = minimum_order

    def discount_for(self, order: Order) -> Decimal:
        # 최소 주문 금액을 못 넘으면 할인 없음
        if order.subtotal < self.minimum_order:
            return Decimal("0")
        return self.amount


class FirstOrderOff:
    """첫 주문이면 정액 할인. 첫 주문 여부는 밖에서 주입받는다 (Dependency Inversion)."""

    def __init__(
        self,
        is_first_order: Callable[[str], bool],
        amount: Decimal = Decimal("3000"),
    ) -> None:
        self.is_first_order = is_first_order
        self.amount = amount

    def discount_for(self, order: Order) -> Decimal:
        if not self.is_first_order(order.customer_id):
            return Decimal("0")
        return self.amount


class BestOf:
    """여러 정책 중 고객에게 가장 유리한 것 하나를 고른다 (Composite)."""

    def __init__(self, *policies: DiscountPolicy) -> None:
        self.policies = policies

    def discount_for(self, order: Order) -> Decimal:
        amounts = [policy.discount_for(order) for policy in self.policies]
        return max(amounts, default=Decimal("0"))


COUPONS: dict[str, DiscountPolicy] = {
    "WELCOME10": PercentOff(10),
    "SAVE5000": FixedAmountOff(Decimal("5000"), minimum_order=Decimal("30000")),
}


def policy_for(
    order: Order,
    *,
    is_first_order: Callable[[str], bool] | None = None,
) -> DiscountPolicy:
    """Factory: 주문 정보를 보고 적용할 정책을 만든다.

    is_first_order를 넘기면 첫 주문 할인도 후보에 넣는다. 안 넘기면 기존과 똑같이 동작한다.
    """
    candidates: list[DiscountPolicy] = []
    if is_first_order is not None:
        candidates.append(FirstOrderOff(is_first_order))
    if order.is_member:
        candidates.append(PercentOff(5))
    if order.coupon_code is not None:
        coupon = COUPONS.get(order.coupon_code)
        if coupon is None:
            raise ValueError(f"unknown coupon: {order.coupon_code}")
        candidates.append(coupon)
    if not candidates:
        return NoDiscount()
    return BestOf(*candidates)
