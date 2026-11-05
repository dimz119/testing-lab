# testing-lab — 테스트 전략과 리팩터링 실습 리포

온라인 서점 주문 도메인으로 테스트 전략 6편을 실습한다. 모든 테스트는 GitHub Actions에서 단계별로 돈다.

| 편 | 주제 | 실습 파일 |
| --- | --- | --- |
| EP1 | 테스트 피라미드 | `tests/` 구조, `pyproject.toml`의 marker, `.github/workflows/ci.yml` |
| EP2 | pytest fixture·parametrize | `tests/conftest.py`, `tests/unit/test_pricing.py` |
| EP3 | mock의 경계 | `src/shop/payment.py`, `tests/unit/test_checkout.py` |
| EP4 | Testcontainers 통합 테스트 | `src/shop/repository.py`, `tests/integration/test_order_repository.py` |
| EP5 | SOLID와 디자인 패턴 핵심 5개 | `src/shop/discounts.py`, `tests/unit/test_discounts.py` |
| EP6 | 레거시 리팩터링 실전 | `src/shop/legacy/invoice.py` → `src/shop/invoice.py`, `tests/unit/test_invoice_characterization.py` |

## 시작하기

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# 단위 테스트만 (1초 이내)
pytest -m "not integration"

# 통합 테스트 (Docker 필요)
pytest -m integration

# CI와 같은 커버리지 기준
pytest -m "not integration" --cov --cov-fail-under=90
```

Docker가 없으면 통합 테스트는 skip된다. CI에서는 `REQUIRE_DOCKER=1`이라 skip 대신 실패한다.

## CI 구조

```
lint (ruff) ──▶ unit (Python 3.12 · 3.13, 커버리지 90%) ──▶ integration (Testcontainers)
```

리포 설정 → Rules → Rulesets에서 `main`에 "Require status checks to pass"를 켜고
`lint`, `unit (3.12)`, `unit (3.13)`, `integration`을 필수 체크로 추가하면, 테스트가 실패한 PR은 merge할 수 없다.

## 깨뜨려 보기 (편마다 브랜치 하나, PR 하나)

각 실습은 브랜치를 만들어 PR을 올리고, CI가 어디서 멈추는지 확인한 뒤 되돌린다.

| 편 | 이렇게 바꾸면 | CI에서 일어나는 일 |
| --- | --- | --- |
| EP1 | 아무 파일에 `import os`만 추가 | `lint`에서 멈춤. `unit`·`integration`은 시작도 안 함 |
| EP2 | `pricing.py`의 `>= FREE_SHIPPING_THRESHOLD`를 `>`로 | `test_shipping_fee_boundary[at-threshold]` 등 2개 실패 |
| EP3 | `CheckoutService.checkout`에서 `save`를 `charge`보다 먼저 호출 | `test_failed_payment_does_not_save_order` 실패 |
| EP4 | `repository.py` 스키마에서 `CHECK (total >= 0)` 삭제 | `unit`은 통과, `integration`에서만 실패 |
| EP5 | `discounts.py`에 새 정책 클래스를 추가하고 `COUPONS`에 등록 | 기존 테스트는 그대로 통과, 새 테스트만 추가 |
| EP6 | `invoice.py`의 `>= FREE_SHIPPING_THRESHOLD`를 `>`로 | `test_refactored_matches_legacy[47000-1-0-False]` 실패 |
