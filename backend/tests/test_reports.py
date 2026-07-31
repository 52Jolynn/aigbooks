"""举报限流逻辑测试。"""

import pytest

pytestmark = pytest.mark.asyncio


async def test_rate_limit_check_unit(db_session):
    """限流逻辑：未超限时通过；超限时抛 429。"""
    from app.middleware.rate_limit import check_report_rate_limit

    await check_report_rate_limit(db_session, "1.2.3.4", "fp12345678")
