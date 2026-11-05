"""EP2 · pytest fixture와 parametrize."""

from decimal import Decimal

import pytest

from shop.discounts import FixedAmountOff, PercentOff
from shop.models import Item, Order
from shop.pricing import calculate_total, shipping_fee


def test_book_fixture_subtotal(book):
    assert book.subtotal == Decimal("33000")


# 경계값 바로 아래·정확히·바로 위를 표 하나로 검사한다
@pytest.mark.parametrize(
    ("amount", "expected_fee"),
    [
        ("49999", "3000"),
        ("50000", "0"),
        ("50001", "0"),
    ],
    ids=["below-threshold", "at-threshold", "above-threshold"],
)
def test_shipping_fee_boundary(amount, expected_fee):
    assert shipping_fee(Decimal(amount)) == Decimal(expected_fee)


@pytest.mark.parametrize(
    ("amount", "quantity", "expected"),
    [
        ("20000", 1, "23000"),
        ("25000", 2, "50000"),
        ("10000", 3, "33000"),
    ],
)
def test_total_without_discount(make_order, amount, quantity, expected):
    order = make_order(amount=amount, quantity=quantity)
    assert calculate_total(order) == Decimal(expected)


def test_percent_discount_can_remove_free_shipping(make_order):
    # 55,000원 - 10% = 49,500원 → 할인 때문에 배송비가 다시 붙는다
    order = make_order(amount="55000")
    assert calculate_total(order, PercentOff(10)) == Decimal("52500")


def test_discount_never_makes_total_negative(make_order):
    order = make_order(amount="3000")
    total = calculate_total(order, FixedAmountOff(Decimal("5000")))
    assert total == Decimal("3000")


def test_empty_order_is_rejected():
    order = Order(order_id="ORD-0", customer_id="C-1", items=[])
    with pytest.raises(ValueError, match="no items"):
        calculate_total(order)


@pytest.mark.parametrize("quantity", [0, -1])
def test_item_rejects_non_positive_quantity(quantity):
    with pytest.raises(ValueError):
        Item(sku="X", title="X", unit_price=Decimal("1000"), quantity=quantity)
