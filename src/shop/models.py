from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class Item:
    sku: str
    title: str
    unit_price: Decimal
    quantity: int

    def __post_init__(self) -> None:
        # 잘못된 값은 만들어지는 순간 막는다
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.unit_price < 0:
            raise ValueError("unit_price must not be negative")

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass
class Order:
    order_id: str
    customer_id: str
    items: list[Item] = field(default_factory=list)
    coupon_code: str | None = None
    is_member: bool = False

    @property
    def subtotal(self) -> Decimal:
        return sum((item.subtotal for item in self.items), Decimal("0"))
