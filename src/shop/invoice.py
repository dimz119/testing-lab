"""EP6 · legacy/invoice.py 를 리팩터링한 결과. 동작은 같고, 규칙에 이름이 생겼다."""

from dataclasses import dataclass
from enum import IntEnum

PERCENT_COUPON_RATE = 0.10
FIXED_COUPON_AMOUNT = 5000
COUPON_MINIMUM_ORDER = 30000
MEMBER_RATE = 0.05
FREE_SHIPPING_THRESHOLD = 50000
SHIPPING_FEE = 3000
WON_PER_POINT = 100
MAX_POINTS = 5000


class CouponType(IntEnum):
    NONE = 0
    PERCENT = 1
    FIXED = 2


@dataclass(frozen=True)
class Line:
    title: str
    unit_price: int
    quantity: int

    @property
    def amount(self) -> int:
        return self.unit_price * self.quantity


def _billable(lines: list[Line]) -> list[Line]:
    # 수량이 0 이하인 줄은 청구하지 않는다 (레거시 동작 유지)
    return [line for line in lines if line.quantity > 0]


def _coupon_discount(subtotal: int, coupon: CouponType) -> float:
    if subtotal < COUPON_MINIMUM_ORDER:
        return 0
    if coupon is CouponType.PERCENT:
        return subtotal * PERCENT_COUPON_RATE
    if coupon is CouponType.FIXED:
        return FIXED_COUPON_AMOUNT
    return 0


def _discount(subtotal: int, coupon: CouponType, is_member: bool) -> float:
    discount = _coupon_discount(subtotal, coupon)
    if is_member:
        discount = max(discount, subtotal * MEMBER_RATE)
    return discount


def _shipping(amount: float) -> int:
    # 결제할 금액이 0원이면 배송비도 받지 않는다 (레거시 동작 유지)
    if amount == 0:
        return 0
    if amount > FREE_SHIPPING_THRESHOLD:
        return 0
    return SHIPPING_FEE


def _round_half_up(value: float) -> int:
    return int(value + 0.5)


def _points(amount: float, is_member: bool) -> int:
    if not is_member:
        return 0
    return min(int(amount / WON_PER_POINT), MAX_POINTS)


def make_invoice(customer: str, lines: list[Line], coupon: CouponType, is_member: bool) -> str:
    billable = _billable(lines)
    subtotal = sum(line.amount for line in billable)
    discount = _discount(subtotal, coupon, is_member)
    amount = max(subtotal - discount, 0)
    shipping = _shipping(amount)
    total = _round_half_up(amount + shipping)
    points = _points(amount, is_member)

    output = [f"INVOICE for {customer}"]
    for line in billable:
        output.append(f"  {line.title} x{line.quantity} = {line.amount}")
    output.append(f"  discount: -{_round_half_up(discount)}")
    output.append(f"  shipping: {shipping}")
    output.append(f"TOTAL: {total}")
    if points > 0:
        output.append(f"points earned: {points}")
    return "\n".join(output)
