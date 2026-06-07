# ModelPulse

AI 端点健康检查、模型测速、错误诊断面板。

面向 OpenAI-compatible API、Hermes/OpenClaw/CLI Proxy 用户。先验证端点能不能用，再决定把哪个模型设为主力。

## MVP 功能

- `/v1/models` 连通性检查
- `/v1/chat/completions` 模型测速
- HTTP 错误码中文诊断
- 推荐当前可用且延迟最低的模型
- 本地 Web 工作台

## 错误码解释

- 400：请求参数/格式有问题
- 401：没登录或 token/key 无效
- 403：没权限或被禁止
- 413：请求体太大
- 502：网关拿到上游错误响应
- 503：服务当前不可用，通常是临时状态
- 504：网关等上游超时

## 本地运行

```bash
uv sync
uv run uvicorn modelpulse.main:app --host 127.0.0.1 --port 8767
python3 -m http.server 8766 --bind 127.0.0.1 --directory apps/web
```

打开：

```text
http://127.0.0.1:8766
```

## 测试

```bash
uv run pytest -q
```

## 项目结构

```text
apps/api/modelpulse/
  diagnostics.py
  prober.py
  main.py
apps/api/tests/
apps/web/
```

## 安全说明

当前 MVP 不持久化 API key。前端提交的 key 只用于当次测速请求。
