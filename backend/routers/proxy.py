import json
import httpx
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from backend.database import get_session
from backend.models import ProviderConfig, UsageRecord
from backend.services.cost import calculate_cost

router = APIRouter(prefix="/proxy")

client = httpx.AsyncClient(timeout=120)


def _is_anthropic_format(headers: dict, body: bytes) -> bool:
    """检测请求是否为 Anthropic Messages 格式"""
    # 通过请求头检测
    if "anthropic-version" in headers or "anthropic-beta" in headers:
        return True
    # 通过请求体结构检测
    try:
        data = json.loads(body)
        if "max_tokens" in data and "messages" in data and "model" in data:
            return True
    except Exception:
        pass
    return False


def _record_usage(session: Session, provider_id: int, provider_name: str, usage: dict, model: str = "", currency: str = "USD",
                   pricing_hit: float = 0.02, pricing_miss: float = 1.0, pricing_out: float = 2.0):
    if not usage:
        return

    prompt_tokens = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
    completion_tokens = usage.get("completion_tokens") or usage.get("output_tokens") or 0
    # 支持 OpenAI 格式和 Anthropic 格式的 cache tokens 字段名
    prompt_cache_hit_tokens = usage.get("prompt_cache_hit_tokens") or usage.get("cache_read_input_tokens") or 0
    prompt_cache_miss_tokens = usage.get("prompt_cache_miss_tokens") or usage.get("cache_creation_input_tokens") or 0
    total_tokens = usage.get("total_tokens") or (prompt_tokens + completion_tokens)

    if total_tokens == 0:
        return

    record = UsageRecord(
        provider_id=provider_id,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        prompt_cache_hit_tokens=prompt_cache_hit_tokens,
        prompt_cache_miss_tokens=prompt_cache_miss_tokens,
        total_tokens=total_tokens,
        cost_usd=calculate_cost(
            prompt_cache_hit_tokens,
            prompt_cache_miss_tokens,
            completion_tokens,
            pricing_hit,
            pricing_miss,
            pricing_out,
        ),
    )
    session.add(record)
    session.commit()
    print(f"[Proxy] Usage recorded: {model} | {total_tokens} tokens | cost={record.cost_usd:.6f} {currency}")


@router.api_route("/{provider_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_request(
    provider_name: str,
    path: str,
    request: Request,
    session: Session = Depends(get_session),
):
    provider = session.exec(select(ProviderConfig).where(ProviderConfig.name == provider_name)).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    if not provider.is_enabled:
        raise HTTPException(status_code=403, detail="Provider disabled")

    headers = dict(request.headers)
    headers.pop("host", None)
    body = await request.body()

    # 检测是否为 Anthropic Messages 格式
    is_anthropic = _is_anthropic_format(headers, body)

    if is_anthropic:
        # Anthropic 格式：转发到 base_url/anthropic/{path}
        target_url = f"{provider.base_url}/anthropic/{path}"
        if request.query_params:
            target_url += f"?{request.query_params}"
        print(f"[Proxy] Anthropic format: {request.method} {target_url}")
    else:
        # OpenAI 格式：原逻辑
        target_url = f"{provider.base_url}/{path}"
        if request.query_params:
            target_url += f"?{request.query_params}"
        print(f"[Proxy] OpenAI format: {request.method} {target_url}")

    # 认证头：Anthropic 使用 x-api-key，OpenAI 使用 Authorization: Bearer
    if is_anthropic:
        headers["x-api-key"] = provider.api_key
    else:
        headers["authorization"] = f"Bearer {provider.api_key}"

    is_stream = False
    try:
        json_body = await request.json()
        is_stream = json_body.get("stream", False)
        # 仅对 OpenAI 格式注入 stream_options（Anthropic 格式有 max_tokens 字段）
        if is_stream and "max_tokens" not in json_body:
            stream_options = json_body.get("stream_options", {})
            if stream_options.get("include_usage") is not True:
                json_body["stream_options"] = {"include_usage": True}
                body = json.dumps(json_body).encode("utf-8")
                headers["content-length"] = str(len(body))
    except Exception:
        pass

    # 流式请求
    if is_stream:
        req = client.build_request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
        )
        proxy_response = await client.send(req, stream=True)

        content_type = proxy_response.headers.get("content-type", "")
        status_code = proxy_response.status_code
        resp_headers = {
            k: v
            for k, v in proxy_response.headers.items()
            if k.lower() not in ("content-encoding", "transfer-encoding", "content-length")
        }

        if "text/event-stream" in content_type:
            model_name = ""
            last_usage = None

            async def stream_with_usage():
                nonlocal model_name, last_usage
                try:
                    async for raw_chunk in proxy_response.aiter_raw():
                        yield raw_chunk
                        try:
                            text = raw_chunk.decode("utf-8", errors="ignore")
                            for line in text.split("\n"):
                                if not line.startswith("data: "):
                                    continue
                                data_str = line[6:].strip()
                                if not data_str or data_str == "[DONE]":
                                    continue
                                chunk_data = json.loads(data_str)
                                # OpenAI 格式
                                if chunk_data.get("model"):
                                    model_name = chunk_data["model"]
                                if chunk_data.get("usage"):
                                    last_usage = chunk_data["usage"]
                                # Anthropic 格式：message_start 包含 model
                                if chunk_data.get("type") == "message_start":
                                    msg = chunk_data.get("message", {})
                                    if msg.get("model"):
                                        model_name = msg["model"]
                                # Anthropic 格式：message_delta 包含 usage
                                if chunk_data.get("type") == "message_delta":
                                    usage = chunk_data.get("usage")
                                    if usage:
                                        last_usage = usage
                        except Exception:
                            pass
                finally:
                    await proxy_response.aclose()
                if last_usage:
                    _record_usage(session, provider.id, provider.name, last_usage, model_name,
                                 provider.balance_currency, provider.pricing_cache_hit_input,
                                 provider.pricing_cache_miss_input, provider.pricing_output)

            return StreamingResponse(
                stream_with_usage(),
                status_code=status_code,
                headers=resp_headers,
            )
        else:
            # 非 SSE 流式响应：读取后返回
            await proxy_response.aread()
            await proxy_response.aclose()
            return Response(
                content=proxy_response.content,
                status_code=status_code,
                headers=resp_headers,
            )

    # 非流式请求
    try:
        proxy_response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Proxy error: {exc}")

    content_type = proxy_response.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            data = proxy_response.json()
            _record_usage(session, provider.id, provider.name, data.get("usage"), data.get("model", ""),
                         provider.balance_currency, provider.pricing_cache_hit_input,
                         provider.pricing_cache_miss_input, provider.pricing_output)
        except Exception:
            pass

    response_headers = {
        k: v
        for k, v in proxy_response.headers.items()
        if k.lower() not in ("content-encoding", "transfer-encoding", "content-length")
    }
    return Response(
        content=proxy_response.content,
        status_code=proxy_response.status_code,
        headers=response_headers,
    )
