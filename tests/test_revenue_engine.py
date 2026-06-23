from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

pytest.importorskip(
    "sqlalchemy", reason="SQLAlchemy backend dependencies are not installed"
)
from hyba_genesis_api.analytics.revenue_engine import RevenueAnalytics


class ScalarQuery:
    def __init__(self, value):
        self.value = value

    def filter(self, *_args, **_kwargs):
        return self

    def scalar(self):
        return self.value


class Session:
    def __init__(self, values):
        self.values = list(values)

    def query(self, *_args, **_kwargs):
        return ScalarQuery(self.values.pop(0))


def test_revenue_engine_degrades_without_commercial_models() -> None:
    analytics = RevenueAnalytics(Session([]))

    assert analytics.compute_arr() == 0.0
    assert analytics.customer_ltv("tenant") == 0.0
    assert analytics.churn_risk_score("tenant") == 100
    assert analytics.unit_economics() == {"cac": 5000.0, "ltv": 0.0, "ratio": 0.0}
