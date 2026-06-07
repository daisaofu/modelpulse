from __future__ import annotations

import time
from typing import Any

import httpx
from pydantic import BaseModel, Field

from modelpulse.diagnostics import explain_status, rank_results


class EndpointConfig(BaseModel):
    name: str
    base_url: str
    api_key: str = ""
    models: list[str] = Field(default_factory=list)


class ModelProbeResult(BaseModel):
    model: str
    ok: bool
    status_code: int | None = None
    latency_ms: float
    error: str | None = None
    response_preview: str | None = None


class EndpointReport(BaseModel):
    name: str
    base_url: str
    models_ok: bool
    models_error: str | None = None
    available_models: list[str] = Field(default_factory=list)
    results: list[ModelProbeResult] = Field(default_factory=list)
    recommended_model: str | None = None


def _join_url(base_url: str, path: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/v1") and path.startswith("/v1/"):
        path = path[3:]
    return f"{base}{path}"


def _headers(api_key: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _extract_models(payload: dict[str, Any]) -> list[str]:
    data = payload.get("data") or []
    return [item["id"] for item in data if isinstance(item, dict) and item.get("id")]


async def probe_endpoint(config: EndpointConfig, client: httpx.AsyncClient | None = None) -> EndpointReport:
    own_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=30)

    try:
        report = EndpointReport(name=config.name, base_url=config.base_url, models_ok=False)
        models_url = _join_url(config.base_url, "/v1/models")
        models_response = await client.get(models_url, headers=_headers(config.api_key))
        report.models_ok = models_response.status_code == 200
        if report.models_ok:
            report.available_models = _extract_models(models_response.json())
        else:
            report.models_error = explain_status(models_response.status_code)

        target_models = config.models or report.available_models[:3]
        for model in target_models:
            report.results.append(await _probe_model(config, model, client))

        ranked = rank_results([item.model_dump() for item in report.results])
        report.recommended_model = next((item["model"] for item in ranked if item.get("ok")), None)
        return report
    finally:
        if own_client:
            await client.aclose()


async def _probe_model(config: EndpointConfig, model: str, client: httpx.AsyncClient) -> ModelProbeResult:
    started = time.perf_counter()
    try:
        response = await client.post(
            _join_url(config.base_url, "/v1/chat/completions"),
            headers=_headers(config.api_key),
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Reply with pong."}],
                "temperature": 0,
                "max_tokens": 16,
            },
        )
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        ok = 200 <= response.status_code < 300
        preview = None
        if ok:
            preview = str(response.json())[:200]
        return ModelProbeResult(
            model=model,
            ok=ok,
            status_code=response.status_code,
            latency_ms=latency_ms,
            error=None if ok else explain_status(response.status_code),
            response_preview=preview,
        )
    except httpx.TimeoutException:
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return ModelProbeResult(model=model, ok=False, latency_ms=latency_ms, error=explain_status(504))
    except httpx.HTTPError as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return ModelProbeResult(model=model, ok=False, latency_ms=latency_ms, error=str(exc))
