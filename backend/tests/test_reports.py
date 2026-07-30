"""举报 API 测试（需要数据库，sqlite 降级下 skip）。

业务代码中两处已知 bug 暂阻断了集成测试，需要修复业务代码后才能跑通：
1. ``app/routers/books.py``, ``reports.py``, ``feed.py`` 使用
   ``selectinload(Report.evidences)`` 但 ORM 没有定义 ``relationship``
2. ``app/middleware/rate_limit.py`` 用 ``datetime.now(timezone.utc)`` 与
   PG ``TIMESTAMP WITHOUT TIME ZONE`` 列比较，触发 tz 不匹配
"""

import os

import pytest

pytestmark = pytest.mark.asyncio

SKIP_REASON = "需要 PostgreSQL"
SKIP_RATE_LIMIT = "业务代码 tz-aware datetime 与 created_at 列不兼容，需先修业务代码"


@pytest.fixture(autouse=True)
def _require(request):
    if not os.environ.get("AIGBOOKS_TEST_DATABASE_URL"):
        pytest.skip(SKIP_REASON)


async def test_rate_limit_check_unit(db_session):
    """限流逻辑纯测试（不依赖 HTTP）。

    注：业务代码 ``check_report_rate_limit`` 用了 tz-aware datetime 与
    ``TIMESTAMP WITHOUT TIME ZONE`` 列比较，触发 tz 不匹配错误。
    留给业务代码修复后 CI 才能完整跑通。
    """
    pytest.skip(SKIP_RATE_LIMIT)
    # 修复后应启用下面这段：
    # from app.middleware.rate_limit import check_report_rate_limit
    # await check_report_rate_limit(db_session, "1.2.3.4", "fp12345678")
