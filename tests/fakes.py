"""Offline stand-ins for the IGVF Catalog API used by the tests."""

import json
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from igvf_catalog_async_client.rest import RESTResponse


class FakeResponse:
    """Stand-in for the aiohttp response returned by the generated *_without_preload_content methods."""

    def __init__(self, payload, status=200, reason='OK'):
        self.status = status
        self.reason = reason
        self.headers = {'Content-Type': 'application/json', 'X-Test': 'header'}
        self.body = json.dumps(payload).encode('utf-8')

    async def read(self):
        return self.body


class FakeCatalog:
    """Offline IGVF Catalog API: maps API paths (without /api) to JSON payloads and records requests."""

    def __init__(self):
        self.responses: dict[str, list[tuple[dict[str, str], Any, int]]] = {}
        self.requests: list[tuple[str, dict[str, str]]] = []

    def add(self, path: str, payload: Any, status: int = 200, params: dict[str, str] | None = None):
        """Respond to requests for path; with params, only to requests that include those query parameters."""
        self.responses.setdefault(path, []).insert(0, (params or {}, payload, status))

    def response_for(self, path: str, params: dict[str, str]) -> tuple[Any, int]:
        """The latest response added for path whose params match the most query parameters."""
        matching = [response for response in self.responses.get(path, []) if response[0].items() <= params.items()]
        if not matching:
            return [], 200
        _, payload, status = max(matching, key=lambda response: len(response[0]))
        return payload, status

    def params_for(self, path: str) -> list[dict[str, str]]:
        return [params for request_path, params in self.requests if request_path == path]

    async def call_api(self, api_client, method, url, header_params=None, body=None, post_params=None,
                       _request_timeout=None):
        parsed = urlsplit(url)
        path = parsed.path.removeprefix('/api')
        params = dict(parse_qsl(parsed.query))
        self.requests.append((path, params))
        payload, status = self.response_for(path, params)
        return RESTResponse(FakeResponse(payload, status=status, reason='OK' if status < 400 else 'Error'))

