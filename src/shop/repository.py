"""EP4 · 저장소.

같은 인터페이스로 메모리 구현(단위 테스트용)과 PostgreSQL 구현(통합 테스트용)을 둔다.
"""

from decimal import Decimal

import psycopg

from shop.models import Order

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    order_id    TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    total       NUMERIC(12, 0) NOT NULL CHECK (total >= 0),
    payment_id  TEXT NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""


class DuplicateOrderError(Exception):
    pass


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self.rows: dict[str, tuple[str, Decimal, str]] = {}

    def save(self, order: Order, total: Decimal, payment_id: str) -> None:
        if order.order_id in self.rows:
            raise DuplicateOrderError(order.order_id)
        self.rows[order.order_id] = (order.customer_id, total, payment_id)

    def total_spent_by(self, customer_id: str) -> Decimal:
        totals = [total for cid, total, _ in self.rows.values() if cid == customer_id]
        return sum(totals, Decimal("0"))


class PostgresOrderRepository:
    def __init__(self, conn: psycopg.Connection) -> None:
        self.conn = conn

    def create_schema(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute(SCHEMA)
        self.conn.commit()

    def save(self, order: Order, total: Decimal, payment_id: str) -> None:
        sql = """
            INSERT INTO orders (order_id, customer_id, total, payment_id)
            VALUES (%s, %s, %s, %s)
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (order.order_id, order.customer_id, total, payment_id))
            self.conn.commit()
        except psycopg.errors.UniqueViolation as exc:
            self.conn.rollback()
            raise DuplicateOrderError(order.order_id) from exc

    def total_spent_by(self, customer_id: str) -> Decimal:
        sql = "SELECT COALESCE(SUM(total), 0) FROM orders WHERE customer_id = %s"
        with self.conn.cursor() as cur:
            cur.execute(sql, (customer_id,))
            row = cur.fetchone()
        return Decimal(row[0])
