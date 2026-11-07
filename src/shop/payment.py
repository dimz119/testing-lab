"""EP3 · 외부 결제 API와의 경계. mock은 '우리가 소유하지 않은 것'의 경계에만 둔다."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

import httpx

from shop.discounts import policy_for
from shop.models import Order
from shop.pricing import calculate_total


class PaymentError(Exception):
    pass


@dataclass(frozen=True)
class PaymentResult:
    payment_id: str
    amount: Decimal


class PaymentGateway(Protocol):
    def charge(self, order_id: str, amount: Decimal, idempotency_key: str) -> PaymentResult: ...


class HttpPaymentGateway:
    """실제 결제사 HTTP API를 감싸는 어댑터 (Adapter)."""

    def __init__(self, client: httpx.Client) -> None:
        self.client = client

    def charge(self, order_id: str, amount: Decimal, idempotency_key: str) -> PaymentResult:
        headers = {"Idempotency-Key": idempotency_key}
        payload = {"order_id": order_id, "amount": str(amount)}
        try:
            response = self.client.post("/v1/charges", json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            raise PaymentError("payment timed out") from exc
        if response.status_code == 402:
            raise PaymentError("card declined")
        response.raise_for_status()
        body = response.json()
        return PaymentResult(payment_id=body["id"], amount=Decimal(body["amount"]))


class OrderRepository(Protocol):
    def save(self, order: Order, total: Decimal, payment_id: str) -> None: ...


class CheckoutService:
    def __init__(self, gateway: PaymentGateway, repository: OrderRepository) -> None:
        self.gateway = gateway
        self.repository = repository

    def checkout(self, order: Order) -> PaymentResult:
        total = calculate_total(order, policy_for(order))
        # 같은 주문을 두 번 결제하지 않도록 주문 ID를 멱등 키로 쓴다
        self.repository.save(order, total, payment_id="pending")
        return self.gateway.charge(order.order_id, total, idempotency_key=order.order_id)
