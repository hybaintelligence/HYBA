from __future__ import annotations
import json as jsonlib
import time
import urllib.error
import urllib.request
from typing import Any

class HYBAServiceError(Exception): pass
class HYBAAuthError(HYBAServiceError): pass
class HYBARateLimitError(HYBAServiceError): pass
class HYBAQuotaExhaustedError(HYBAServiceError): pass

class _Namespace:
    def __init__(self, client: "HYBAClient") -> None: self._client = client

class _QaaS(_Namespace):
    def execute(self, circuit_spec: dict[str, Any]) -> dict[str, Any]:
        computer_id = circuit_spec.get("computer_id")
        payload = {k:v for k,v in circuit_spec.items() if k != "computer_id"}
        if computer_id:
            return self._client.request("POST", f"/api/v1/fault-tolerant-computers/{computer_id}/execute", json=payload)
        computer = self._client.request("POST", "/api/v1/fault-tolerant-computers", json={"name":"sdk-computer"})
        self._client.request("POST", f"/api/v1/fault-tolerant-computers/{computer['computer_id']}/start")
        return self._client.request("POST", f"/api/v1/fault-tolerant-computers/{computer['computer_id']}/execute", json=payload or {"operation":"surface_code_cycle"})

class _QIaaS(_Namespace):
    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._client.request("POST", "/api/qiaas/query", json={"query_type":"predict", "context":payload})

class _Finance(_Namespace):
    def portfolio_optimize(self, weights: list[float], constraints: dict[str, Any]) -> dict[str, Any]:
        n=len(weights); cov=constraints.get("covariance_matrix") or [[1.0 if i==j else 0.0 for j in range(n)] for i in range(n)]
        body={"expected_returns":weights,"covariance_matrix":cov,"budget":constraints.get("budget",max(1,min(n,1))), **{k:v for k,v in constraints.items() if k!="covariance_matrix"}}
        return self._client.request("POST", "/api/quantum-finance/portfolio/qaoa-design", json=body)

class HYBAClient:
    def __init__(self, api_key: str, base_url: str = "https://api.hyba.ai", timeout: float = 30.0) -> None:
        if not api_key: raise HYBAAuthError("api_key is required")
        self.api_key=api_key; self.base_url=base_url.rstrip('/'); self.timeout=timeout
        self.qaas=_QaaS(self); self.qiaas=_QIaaS(self); self.finance=_Finance(self)
    def request(self, method: str, path: str, json: Any | None=None) -> dict[str, Any]:
        body = None if json is None else jsonlib.dumps(json).encode("utf-8")
        headers={"X-API-Key": self.api_key, "Accept":"application/json", "Content-Type":"application/json"}
        for attempt in range(4):
            req=urllib.request.Request(self.base_url+path, data=body, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    raw=response.read().decode("utf-8")
                    return jsonlib.loads(raw) if raw else {}
            except urllib.error.HTTPError as exc:
                text=exc.read().decode("utf-8", errors="replace")
                if exc.code == 429 and attempt < 3:
                    time.sleep(min(2**attempt, 8)); continue
                if exc.code in (401,403): raise HYBAAuthError(text) from exc
                if exc.code == 429: raise HYBARateLimitError(text) from exc
                if exc.code == 402: raise HYBAQuotaExhaustedError(text) from exc
                raise HYBAServiceError(text) from exc
        raise HYBARateLimitError("rate limit retry budget exhausted")
