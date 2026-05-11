import json
import httpx
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from backend.database import get_session
from backend.models import ProviderConfig, UsageRecord
from backend.services.cost import calculate_cost

router = APIRouter(prefix="/proxy")

client = httpx.AsyncClient(timeout=60)


def _record_usage(session: Session, provider_id: int, provider_name: str, usage: dict, model: str = "", currency: str = "USD"):
    if not usage:
        return

    # 兼容 OpenAI 格式和 Anthropic 格式
    prompt_tokens = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
    completion_tokens = usage.get("completion_tokens") or usage.get("output_tokens") or 0
    prompt_cache_hit_tokens = usage.get("prompt_cache_hit_tokens", 0)
    prompt_cache_miss_tokens = usage.get("prompt_cache_miss_tokens", 0)
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
            provider_name,
            currency,
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
        print(f"[Proxy] Provider not found: {provider_name}")
        raise HTTPException(status_code=404, detail="Provider not found")
    if not provider.is_enabled:
        print(f"[Proxy] Provider disabled: {provider_name}")
        raise HTTPException(status_code=403, detail="Provider disabled")

    print(f"[Proxy] {request.method} /proxy/{provider_name}/{path}")

    target_url = f"{provider.base_url}/{path}"
    if request.query_params:
        target_url += f"?{request.query_params}"

    headers = dict(request.headers)
    headers.pop("host", None)
    headers["authorization"] = f"Bearer {provider.api_key}"

    body = await request.body()

    is_stream = False
    try:
        json_body = await request.json()
        is_stream = json_body.get("stream", False)
        # 注入 stream_options 使上游在最后一个 chunk 返回 usage
        if is_stream:
            stream_options = json_body.get("stream_options", {})
            if stream_options.get("include_usage") is not True:
                json_body["stream_options"] = {"include_usage": True}
                body = json.dumps(json_body).encode("utf-8")
                headers["content-length"] = str(len(body))
    except Exception:
        pass

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

    # 非流式响应，直接解析 usage
    if not is_stream and "application/json" in content_type:
        try:
            data = proxy_response.json()
            _record_usage(session, provider.id, provider.name, data.get("usage"), data.get("model", ""), provider.balance_currency)
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

    # 流式响应：逐 chunk 转发，同时捕获最后一个 chunk 的 usage
    if is_stream and "text/event-stream" in content_type:
        model_name = ""
        last_usage = None

        async def stream_with_usage():
            nonlocal model_name, last_usage
            async for raw_chunk in proxy_response.aiter_raw():
                yield raw_chunk
                # 尝试解析 SSE data 行
                try:
                    text = raw_chunk.decode("utf-8", errors="ignore")
                    for line in text.split("\n"):
                        if line.startswith("data: ") and line.strip() != "data: [DONE]":
                            chunk_data = json.loads(line[6:])
                            if chunk_data.get("model"):
                                model_name = chunk_data["model"]
                            if chunk_data.get("usage"):
                                last_usage = chunk_data["usage"]
                except Exception:
                    pass
            # 流结束后记录用量
            if last_usage:
                _record_usage(session, provider.id, provider.name, last_usage, model_name, provider.balance_currency)

        response_headers = {
            k: v
            for k, v in proxy_response.headers.items()
            if k.lower() not in ("content-encoding", "transfer-encoding", "content-length")
        }
        return StreamingResponse(
            stream_with_usage(),
            status_code=proxy_response.status_code,
            headers=response_headers,
        )

    # 兜底：其他响应直接透传
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
