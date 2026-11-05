"""EP4 · Testcontainers 통합 테스트. 진짜 PostgreSQL을 띄워서 SQL·제약 조건을 검증한다.

Docker가 없는 환경에서는 건너뛴다. CI(GitHub Actions ubuntu 러너)에는 Docker가 있다.
"""

import os
from decimal import Decimal

import pytest

from shop.repository import DuplicateOrderError, PostgresOrderRepository

pytestmark = pytest.mark.integration

psycopg = pytest.importorskip("psycopg")
postgres = pytest.importorskip("testcontainers.community.postgres")


def docker_available() -> bool:
    try:
        import docker

        docker.from_env().ping()
    except Exception:
        return False
    return True


# 컨테이너는 비싸므로 모듈 전체에서 한 번만 띄운다
@pytest.fixture(scope="module")
def pg_url():
    if not docker_available():
        # CI에서는 건너뛰지 말고 실패시킨다. 조용히 skip된 통합 테스트는 없는 것과 같다.
        if os.environ.get("REQUIRE_DOCKER") == "1":
            pytest.fail("REQUIRE_DOCKER=1 but Docker daemon is not available")
        pytest.skip("Docker daemon is not available")
    with postgres.PostgresContainer("postgres:17-alpine", driver=None) as container:
        yield container.get_connection_url()


# 테스트마다 테이블을 비워서 서로 영향을 주지 않게 한다
@pytest.fixture
def repository(pg_url):
    with psycopg.connect(pg_url) as conn:
        repo = PostgresOrderRepository(conn)
        repo.create_schema()
        with conn.cursor() as cur:
            cur.execute("TRUNCATE orders")
        conn.commit()
        yield repo


def test_save_and_sum_by_customer(repository, make_order):
    repository.save(make_order(order_id="A", customer_id="C-1"), Decimal("23000"), "pay_A")
    repository.save(make_order(order_id="B", customer_id="C-1"), Decimal("41000"), "pay_B")
    repository.save(make_order(order_id="C", customer_id="C-2"), Decimal("9000"), "pay_C")

    assert repository.total_spent_by("C-1") == Decimal("64000")
    assert repository.total_spent_by("nobody") == Decimal("0")


def test_duplicate_order_is_rejected_by_primary_key(repository, make_order):
    order = make_order(order_id="DUP")
    repository.save(order, Decimal("23000"), "pay_1")

    with pytest.raises(DuplicateOrderError):
        repository.save(order, Decimal("23000"), "pay_2")


def test_negative_total_violates_check_constraint(repository, make_order):
    # 메모리 구현은 이 규칙을 모른다. 진짜 DB로만 잡을 수 있는 버그다.
    with pytest.raises(psycopg.errors.CheckViolation):
        repository.save(make_order(order_id="NEG"), Decimal("-1"), "pay_neg")
