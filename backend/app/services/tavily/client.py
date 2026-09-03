import time
from typing import Any

import httpx

from app.core.config import settings


class TavilyClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.tavily_api_key
        self.base_url = "https://api.tavily.com"
        self.timeout = httpx.Timeout(settings.tavily_timeout_seconds)

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("TAVILY_API_KEY is not configured")
        body = {"api_key": self.api_key, **payload}
        last_error: Exception | None = None
        for attempt in range(settings.tavily_retries):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(f"{self.base_url}{path}", json=body)
                    response.raise_for_status()
                    return response.json()
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                last_error = exc
                time.sleep(0.5 * (2**attempt))
        raise RuntimeError(f"Tavily request failed: {last_error}") from last_error

    def search_updates(self, query: str, domains: list[str] | None = None, days: int = 30) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "query": query,
            "max_results": settings.tavily_max_results,
            "search_depth": "advanced",
            "topic": "news",
            "days": days,
        }
        if domains:
            payload["include_domains"] = domains
        return self._post("/search", payload)

    def extract_updates(self, urls: list[str]) -> dict[str, Any]:
        return self._post("/extract", {"urls": urls, "extract_depth": "advanced"})

    def crawl_official_source(self, url: str, allowed_domains: list[str], max_depth: int = 2, max_pages: int = 20) -> dict[str, Any]:
        return self._post(
            "/crawl",
            {
                "url": url,
                "max_depth": max_depth,
                "max_breadth": max_pages,
                "limit": max_pages,
                "instructions": "Find release notes, changelogs, security, migration, and announcement pages.",
                "exclude_paths": ["/blog/tags", "/tags", "/archive"],
                "allow_external": False,
                "include_domains": allowed_domains,
            },
        )
