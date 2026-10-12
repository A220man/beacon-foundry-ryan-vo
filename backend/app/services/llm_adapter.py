import httpx
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from ..core.config import settings
from ..models.schemas import AdvisoryRequest, AdvisoryResponse

async def request_llm_advisory(request: AdvisoryRequest) -> AdvisoryResponse:
    now = datetime.now(timezone.utc).isoformat()
    
    # Check if API key is supplied by operator
    if not settings.llm_api_key or not settings.llm_api_key.strip():
        # Clean informative fallback (never fabricate fake model answers)
        return AdvisoryResponse(
            provider="offline-deterministic",
            model="heuristic-rule-engine",
            advisory_text=(
                "LLM advisory assistance is disabled or LLM_API_KEY is not configured by operator. "
                "Deterministic analysis indicates that the observed Apollo telemetry or AGC syntax pattern "
                "should be verified against the official Luminary 099 / Comanche 055 program listings on ibiblio.org."
            ),
            confidence_assessment="advisory-offline-deterministic",
            timestamp=now
        )

    system_prompt = (
        "You are an Apollo Guidance Computer flight software advisor. Analyze discrepancies or telemetry "
        "deviations using historical guidance computer documentation."
    )
    user_content = f"Context: {request.context_type}\nDetails: {request.details}\nQuery: {request.user_query}"

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            if settings.llm_provider in {"openai-compatible", "ollama"}:
                headers = {
                    "Authorization": f"Bearer {settings.llm_api_key}",
                    "Content-Type": "application/json"
                }
                body = {
                    "model": settings.llm_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    "temperature": 0.2
                }
                resp = await client.post(f"{settings.llm_base_url}/chat/completions", headers=headers, json=body)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    return AdvisoryResponse(
                        provider=settings.llm_provider,
                        model=settings.llm_model,
                        advisory_text=content,
                        confidence_assessment="advisory-llm-grounded",
                        timestamp=now
                    )
                else:
                    return AdvisoryResponse(
                        provider=settings.llm_provider,
                        model=settings.llm_model,
                        advisory_text=f"Provider returned error HTTP {resp.status_code}. Raw response redacted.",
                        confidence_assessment="error",
                        timestamp=now
                    )

            elif settings.llm_provider == "anthropic":
                headers = {
                    "x-api-key": settings.llm_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                body = {
                    "model": settings.llm_model,
                    "max_tokens": 1024,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_content}]
                }
                resp = await client.post(f"{settings.llm_base_url}/v1/messages", headers=headers, json=body)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["content"][0]["text"]
                    return AdvisoryResponse(
                        provider="anthropic",
                        model=settings.llm_model,
                        advisory_text=content,
                        confidence_assessment="advisory-llm-grounded",
                        timestamp=now
                    )
                else:
                    return AdvisoryResponse(
                        provider="anthropic",
                        model=settings.llm_model,
                        advisory_text=f"Anthropic provider returned HTTP {resp.status_code}.",
                        confidence_assessment="error",
                        timestamp=now
                    )

            elif settings.llm_provider == "gemini":
                url = f"{settings.llm_base_url}/v1beta/models/{settings.llm_model}:generateContent?key={settings.llm_api_key}"
                body = {
                    "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_content}"}]}]
                }
                resp = await client.post(url, json=body)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["candidates"][0]["content"]["parts"][0]["text"]
                    return AdvisoryResponse(
                        provider="gemini",
                        model=settings.llm_model,
                        advisory_text=content,
                        confidence_assessment="advisory-llm-grounded",
                        timestamp=now
                    )
                else:
                    return AdvisoryResponse(
                        provider="gemini",
                        model=settings.llm_model,
                        advisory_text=f"Gemini provider returned HTTP {resp.status_code}.",
                        confidence_assessment="error",
                        timestamp=now
                    )

    except Exception as e:
        # Sanitized error report without leaking credentials
        return AdvisoryResponse(
            provider=settings.llm_provider,
            model=settings.llm_model,
            advisory_text=f"Connection failure communicating with {settings.llm_provider}: {type(e).__name__}",
            confidence_assessment="connection-failure",
            timestamp=now
        )

    return AdvisoryResponse(
        provider=settings.llm_provider,
        model=settings.llm_model,
        advisory_text="Unsupported LLM provider configured.",
        confidence_assessment="error",
        timestamp=now
    )
