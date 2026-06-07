ERROR_EXPLANATIONS = {
    400: "请求参数/格式有问题",
    401: "没登录或 token/key 无效",
    403: "没权限或被禁止",
    413: "请求体太大",
    502: "网关拿到上游错误响应",
    503: "服务当前不可用，通常是临时状态",
    504: "网关等上游超时",
}


def explain_status(status_code: int) -> str:
    return ERROR_EXPLANATIONS.get(status_code, "未知错误码")


def rank_results(results: list[dict]) -> list[dict]:
    return sorted(
        results,
        key=lambda item: (
            not bool(item.get("ok")),
            float(item.get("latency_ms") or 999999),
        ),
    )
