import os

import pytest

from app.core.database import test_connection as read_only_connection


pytestmark = pytest.mark.integration


@pytest.mark.skipif(not os.getenv("DB_PASSWORD"), reason="DB_PASSWORD no configurada")
def test_demo_login_is_read_only() -> None:
    result = read_only_connection()

    assert result["database"] == "erp_portfolio_demo"
    assert result["read_only"] is True
    assert result["permissions"]["insert"] is False
    assert result["permissions"]["update"] is False
    assert result["permissions"]["delete"] is False
