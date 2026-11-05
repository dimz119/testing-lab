"""EP2 · 가격 계산. 순수 함수라서 단위 테스트하기 가장 좋은 곳이다."""

import os
from decimal import ROUND_HALF_UP, Decimal

from shop.discounts import DiscountPolicy, NoDiscount
from shop.models import Order

FREE_SHIPPING_THRESHOLD = Decimal("50000")
SHIPPING_FEE = Decimal("3000")


def shipping_fee(amount_after_discount: Decimal) -> Decimal:
    # 경계값: 정확히 50,000원이면 무료 배송
    if amount_after_discount >= FREE_SHIPPING_THRESHOLD:
        return Decimal("0")
    return SHIPPING_FEE


def calculate_total(order: Order, policy: DiscountPolicy | None = None) -> Decimal:
    if not order.items:
        raise ValueError("order has no items")
    # 정책을 주입받는다 (EP5 · 의존성 주입)
    chosen = policy if policy is not None else NoDiscount()
    discount = chosen.discount_for(order)
    # 할인액이 주문 금액을 넘지 않게 막는다
    discount = min(discount, order.subtotal)
    discounted = order.subtotal - discount
    total = discounted + shipping_fee(discounted)
    return total.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
