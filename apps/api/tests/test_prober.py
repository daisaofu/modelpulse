import pytest
import httpx

from modelpulse.prober import EndpointConfig, probe_endpoint


@pytest.mark.asyncio
async def test_probe_endpoint_lists_models_and_tests_chat_completion():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={"data": [{"id": "fast-model"}, {"id": "slow-model"}]})
        if request.url.path == "/v1/chat/completions":
            body = request.read().decode()
            assert "fast-model" in body
            assert request.headers["authorization"] == "Bearer test-key"
            return httpx.Response(200, json={"choices": [{"message": {"content": "pong"}}]})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        report = await probe_endpoint(
            EndpointConfig(name="local", base_url="https://api.example.com/v1", api_key="test-key", models=["fast-model"]),
            client=client,
        )

    assert report.name == "local"
    assert report.models_ok is True
    assert report.available_models == ["fast-model", "slow-model"]
    assert report.results[0].model == "fast-model"
    assert report.results[0].ok is True
    assert report.results[0].status_code == 200
    assert report.recommended_model == "fast-model"


@pytest.mark.asyncio
async def test_probe_endpoint_explains_http_errors():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/models":
            return httpx.Response(401, json={"error": "bad key"})
        return httpx.Response(503, json={"error": "temporarily unavailable"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        report = await probe_endpoint(
            EndpointConfig(name="broken", base_url="https://api.example.com/v1", api_key="bad", models=["x"]),
            client=client,
        )

    assert report.models_ok is False
    assert report.models_error == "没登录或 token/key 无效"
    assert report.results[0].ok is False
    assert report.results[0].error == "服务当前不可用，通常是临时状态"
    assert report.recommended_model is None
