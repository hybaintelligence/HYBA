"""Analytics engine for HYBA revenue optimization.

The engine is intentionally ORM-light: it can consume SQLAlchemy models when they
are present in an installed deployment, and it degrades to zeroed metrics in
local/test environments that do not yet have commercial persistence tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
UTC = timezone.utc, timedelta
from typing import Any

from sqlalchemy import func


@dataclass(frozen=True)
class UnitEconomics:
    """SaaS unit-economics snapshot."""

    cac: float
    ltv: float
    ratio: float

    def as_dict(self) -> dict[str, float]:
        return {"cac": self.cac, "ltv": self.ltv, "ratio": self.ratio}


class RevenueAnalytics:
    """Compute business metrics from operational data."""

    def __init__(self, db_session: Any, assumed_cac_usd: float = 5000.0) -> None:
        self.session = db_session
        self.assumed_cac_usd = float(assumed_cac_usd)

    def _models(self) -> tuple[Any | None, Any | None]:
        """Return optional Tenant and WorkloadExecution ORM classes."""
        try:
            from consciousness_db.models import Tenant, WorkloadExecution  # type: ignore

            return Tenant, WorkloadExecution
        except Exception:
            return None, None

    def compute_arr(self, end_date: datetime | None = None) -> float:
        """Annualize revenue recorded during the trailing 30-day window."""
        if end_date is None:
            end_date = datetime.now(UTC)
        _tenant, workload_execution = self._models()
        if workload_execution is None:
            return 0.0
        monthly_revenue = (
            self.session.query(func.sum(workload_execution.actual_cost))
            .filter(workload_execution.executed_at >= end_date - timedelta(days=30))
            .scalar()
            or 0
        )
        return round(float(monthly_revenue) * 12, 2)

    def customer_ltv(self, tenant_id: str) -> float:
        """Return lifetime spend for a tenant."""
        _tenant, workload_execution = self._models()
        if workload_execution is None:
            return 0.0
        total_spent = (
            self.session.query(func.sum(workload_execution.actual_cost))
            .filter(workload_execution.tenant_id == tenant_id)
            .scalar()
            or 0
        )
        return round(float(total_spent), 2)

    def churn_risk_score(self, tenant_id: str, now: datetime | None = None) -> int:
        """Score 0-100: likelihood that customer will churn based on inactivity."""
        if now is None:
            now = datetime.now(UTC)
        _tenant, workload_execution = self._models()
        if workload_execution is None:
            return 100
        last_activity = (
            self.session.query(func.max(workload_execution.executed_at))
            .filter(workload_execution.tenant_id == tenant_id)
            .scalar()
        )
        if not last_activity:
            return 100
        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=UTC)
        days_inactive = (now - last_activity).days
        if days_inactive > 90:
            return 90
        if days_inactive > 30:
            return 50
        return 10

    def unit_economics(self) -> dict[str, float]:
        """Compute CAC, average LTV, and LTV/CAC ratio."""
        tenant, workload_execution = self._models()
        if tenant is None or workload_execution is None:
            return UnitEconomics(self.assumed_cac_usd, 0.0, 0.0).as_dict()
        total_customers = self.session.query(func.count(tenant.id)).scalar() or 0
        total_revenue = self.session.query(func.sum(workload_execution.actual_cost)).scalar() or 0
        ltv = float(total_revenue) / max(int(total_customers), 1)
        ratio = ltv / self.assumed_cac_usd if self.assumed_cac_usd > 0 else 0.0
        return UnitEconomics(self.assumed_cac_usd, round(ltv, 2), round(ratio, 4)).as_dict()
