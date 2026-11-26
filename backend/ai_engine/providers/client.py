import httpx

from backend.core.config import settings
from backend.ai_engine.prompts.system_prompt import SYSTEM_PROMPT


class AIProviderError(Exception):
    pass


class AIEngine:

    def __init__(self):

        self.providers = {
            "groq": {
                "key": settings.GROQ_API_KEY,
                "url": "https://api.groq.com/openai/v1/chat/completions",
                "model": settings.GROQ_MODEL,
            },
            "openrouter": {
                "key": settings.OPENROUTER_API_KEY,
                "url": "https://openrouter.ai/api/v1/chat/completions",
                "model": settings.OPENROUTER_MODEL,
            },
            "gemini": {
                "key": settings.GEMINI_API_KEY,
                "url": (
                    "https://generativelanguage.googleapis.com/"
                    f"v1beta/models/{settings.GEMINI_MODEL}:generateContent"
                ),
                "model": settings.GEMINI_MODEL,
            }
        }

    def available_providers(self):

        return [
            name
            for name, config in self.providers.items()
            if config["key"]
        ]

    async def _request_provider(self, provider, message, history=None):

        config = self.providers[provider]
        headers = {"Content-Type": "application/json"}
        history = history or []

        if provider == "gemini":

            headers["x-goog-api-key"] = config["key"]

            contents = []

            for item in history:

                role = (
                    "model"
                    if item["role"] == "assistant"
                    else "user"
                )

                contents.append({
                    "role": role,
                    "parts": [{"text": item["content"]}]
                })

            contents.append({
                "role": "user",
                "parts": [{"text": message}]
            })

            payload = {
                "systemInstruction": {
                    "parts": [{"text": SYSTEM_PROMPT}]
                },
                "contents": contents
            }

            url = config["url"]

        else:

            headers["Authorization"] = f"Bearer {config['key']}"

            messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }
            ]

            messages.extend([
                {
                    "role": item["role"],
                    "content": item["content"]
                }
                for item in history
            ])

            messages.append({
                "role": "user",
                "content": message
            })

            payload = {
                "model": config["model"],
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2048
            }

            url = config["url"]

            if provider == "openrouter":

                headers["HTTP-Referer"] = "http://localhost:3000"
                headers["X-Title"] = "AETHERIQ AI"

        async with httpx.AsyncClient(timeout=60.0) as client:

            response = await client.post(
                url,
                headers=headers,
                json=payload
            )

            if response.is_error:

                try:
                    error_data = response.json()
                    error_message = error_data.get(
                        "error", {}
                    ).get(
                        "message",
                        "Unknown provider error"
                    )

                except ValueError:
                    error_message = "Unable to read provider error"

                raise AIProviderError(
                    f"{provider} HTTP "
                    f"{response.status_code}: {error_message}"
                )

            data = response.json()

        if provider == "gemini":

            try:
                answer = (
                    data["candidates"][0]
                    ["content"]["parts"][0]["text"]
                )

            except (KeyError, IndexError, TypeError):
                raise AIProviderError("Invalid Gemini response")

        else:

            try:
                answer = data["choices"][0]["message"]["content"]

            except (KeyError, IndexError, TypeError):
                raise AIProviderError(
                    f"Invalid response from {provider}"
                )

        return {
            "provider": provider,
            "model": config["model"],
            "response": answer
        }

    async def generate(
        self,
        message,
        preferred_provider=None,
        history=None
    ):

        available = self.available_providers()

        if not available:
            raise AIProviderError(
                "No AI provider configured. "
                "Add an API key to your .env file."
            )

        primary = (
            preferred_provider or settings.DEFAULT_PROVIDER
        ).lower()

        if primary not in self.providers:
            raise AIProviderError("Unknown AI provider")

        provider_order = [primary] + [
            name for name in available if name != primary
        ]

        errors = []

        for provider in provider_order:

            if provider not in available:
                continue

            try:
                return await self._request_provider(
                    provider,
                    message,
                    history
                )

            except (httpx.HTTPError, AIProviderError) as error:
                errors.append(f"{provider}: {error}")

        raise AIProviderError(
            "All configured AI providers failed. "
            + " | ".join(errors)
        )


ai_engine = AIEngine()