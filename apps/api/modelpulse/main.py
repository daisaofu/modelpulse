from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from modelpulse.diagnostics import ERROR_EXPLANATIONS
from modelpulse.prober import EndpointConfig, EndpointReport, probe_endpoint

app = FastAPI(title="ModelPulse", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, object]:
    return {"ok": True, "service": "modelpulse"}


@app.get("/api/error-explanations")
def error_explanations() -> dict[str, str]:
    return {str(code): text for code, text in ERROR_EXPLANATIONS.items()}


@app.post("/api/probe", response_model=EndpointReport)
async def probe(config: EndpointConfig) -> EndpointReport:
    return await probe_endpoint(config)
