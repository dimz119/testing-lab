"""EP2 · 여러 테스트 파일이 함께 쓰는 fixture는 conftest.py에 둔다."""

from decimal import Decimal

import pytest

from shop.models import Item, Order


@pytest.fixture
def book() -> Item:
    return Item(sku="BK-001", title="클린 코드", unit_price=Decimal("33000"), quantity=1)


@pytest.fixture
def make_order():
    """원하는 금액의 주문을 한 줄로 만드는 factory fixture."""

    def _make(
        amount: str = "20000",
        quantity: int = 1,
        coupon: str | None = None,
        member: bool = False,
        order_id: str = "ORD-1",
        customer_id: str = "C-1",
    ) -> Order:
        item = Item(sku="BK-X", title="테스트 책", unit_price=Decimal(amount), quantity=quantity)
        return Order(
            order_id=order_id,
            customer_id=customer_id,
            items=[item],
            coupon_code=coupon,
            is_member=member,
        )

    return _make
