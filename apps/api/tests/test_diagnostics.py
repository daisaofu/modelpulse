from modelpulse.diagnostics import explain_status, rank_results


def test_explain_status_returns_clear_chinese_reason_for_known_codes():
    assert explain_status(400) == "请求参数/格式有问题"
    assert explain_status(401) == "没登录或 token/key 无效"
    assert explain_status(403) == "没权限或被禁止"
    assert explain_status(413) == "请求体太大"
    assert explain_status(502) == "网关拿到上游错误响应"
    assert explain_status(503) == "服务当前不可用，通常是临时状态"
    assert explain_status(504) == "网关等上游超时"


def test_explain_status_handles_unknown_codes():
    assert explain_status(418) == "未知错误码"


def test_rank_results_prefers_successful_lower_latency_models():
    results = [
        {"model": "slow-ok", "ok": True, "latency_ms": 1200},
        {"model": "fast-failed", "ok": False, "latency_ms": 100},
        {"model": "fast-ok", "ok": True, "latency_ms": 300},
    ]

    ranked = rank_results(results)

    assert [item["model"] for item in ranked] == ["fast-ok", "slow-ok", "fast-failed"]
