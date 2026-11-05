"""EP3 · mock의 경계.

규칙: 우리가 소유한 코드(가격 계산, 할인)는 진짜로 실행하고,
우리가 소유하지 않은 것(결제사 HTTP API)만 가짜로 바꾼다.
"""

from decimal import Decimal
from unittest.mock import Mock

import httpx
import pytest

from shop.payment import (
    CheckoutService,
    HttpPaymentGateway,
    PaymentError,
    PaymentGateway,
    PaymentResult,
)
from shop.repository import InMemoryOrderRepository

# --- 방법 1 · Fake: 손으로 만든 가벼운 구현. 상태를 확인하기 쉽다 ---


class FakeGateway:
    def __init__(self) -> None:
        self.charges: list[tuple[str, Decimal, str]] = []

    def charge(self, order_id: str, amount: Decimal, idempotency_key: str) -> PaymentResult:
        self.charges.append((order_id, amount, idempotency_key))
        return PaymentResult(payment_id=f"pay_{order_id}", amount=amount)


def test_checkout_charges_discounted_total_and_saves(make_order):
    gateway = FakeGateway()
    repository = InMemoryOrderRepository()
    service = CheckoutService(gateway, repository)
    order = make_order(amount="40000", coupon="WELCOME10")

    result = service.checkout(order)

    # 40,000 - 10% = 36,000 + 배송비 3,000
    assert gateway.charges == [("ORD-1", Decimal("39000"), "ORD-1")]
    assert result.payment_id == "pay_ORD-1"
    assert repository.total_spent_by("C-1") == Decimal("39000")


# --- 방법 2 · Mock: 호출 자체가 검증 대상일 때만 ---


def test_failed_payment_does_not_save_order(make_order):
    gateway = Mock(spec=PaymentGateway)
    gateway.charge.side_effect = PaymentError("card declined")
    repository = Mock()
    service = CheckoutService(gateway, repository)

    with pytest.raises(PaymentError):
        service.checkout(make_order())

    repository.save.assert_not_called()


# --- 방법 3 · 전송 계층 가짜: 어댑터 코드까지 실제로 실행된다 ---


def make_http_gateway(handler) -> HttpPaymentGateway:
    transport = httpx.MockTransport(handler)
    client = httpx.Client(base_url="https://pay.example.com", transport=transport)
    return HttpPaymentGateway(client)


def test_http_gateway_sends_idempotency_key():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["key"] = request.headers["Idempotency-Key"]
        seen["path"] = request.url.path
        return httpx.Response(200, json={"id": "pay_123", "amount": "23000"})

    gateway = make_http_gateway(handler)
    result = gateway.charge("ORD-9", Decimal("23000"), idempotency_key="ORD-9")

    assert seen == {"key": "ORD-9", "path": "/v1/charges"}
    assert result == PaymentResult(payment_id="pay_123", amount=Decimal("23000"))


@pytest.mark.parametrize(
    ("response", "message"),
    [
        (httpx.Response(402, json={"error": "declined"}), "card declined"),
        (httpx.TimeoutException("slow"), "timed out"),
    ],
    ids=["declined", "timeout"],
)
def test_http_gateway_translates_errors(response, message):
    def handler(request: httpx.Request) -> httpx.Response:
        if isinstance(response, Exception):
            raise response
        return response

    gateway = make_http_gateway(handler)
    with pytest.raises(PaymentError, match=message):
        gateway.charge("ORD-9", Decimal("1000"), idempotency_key="ORD-9")


# --- 안티 패턴 · 내부 구현을 mock하면 리팩터링할 때마다 테스트가 깨진다 ---
#
# @patch("shop.payment.calculate_total", return_value=Decimal("39000"))
# def test_checkout_bad(mock_total, ...):
#     ...
#     mock_total.assert_called_once()
#
# 가격 계산은 우리 코드다. 진짜로 돌려서 결과(청구 금액)를 확인하는 게 맞다.
