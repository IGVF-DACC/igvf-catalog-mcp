"""Thin wrapper around the generated async IGVF Catalog client."""

import inspect
import json
import os
from functools import cache
from typing import Any

from igvf_catalog_async_client import ApiClient, AsyncIgvfCatalogApi, Configuration
from igvf_catalog_async_client.exceptions import ApiException
from igvf_catalog_async_client.rest import RESTResponse

DEFAULT_API_URL = 'https://api.catalogkg.igvf.org'


def resolve_base_url(base_url: str | None = None) -> str:
    """
    Resolve the API base URL, including the /api prefix used by the generated client.

    Args:
        base_url: Explicit base URL. Defaults to IGVF_CATALOG_API_URL or production.

    Returns:
        Base URL ending in /api, without a trailing slash
    """
    url = (base_url or os.getenv('IGVF_CATALOG_API_URL') or DEFAULT_API_URL).rstrip('/')
    if not url.endswith('/api'):
        url = f'{url}/api'
    return url


@cache
def method_params(method_name: str) -> frozenset[str]:
    """
    Get the keyword arguments accepted by a generated client method.

    Args:
        method_name: AsyncIgvfCatalogApi method name (e.g., "genes_from_variants")

    Returns:
        Set of accepted parameter names, excluding self and the generator's _-prefixed options
    """
    method = getattr(AsyncIgvfCatalogApi, method_name, None)
    if method is None:
        raise ValueError(f'Unknown IGVF Catalog API method: {method_name}')
    return frozenset(
        name for name in inspect.signature(method).parameters if name != 'self' and not name.startswith('_')
    )


class IGVFCatalogClient:
    """Async client for querying the IGVF Catalog API through the generated client."""

    def __init__(self, base_url: str | None = None, timeout: float = 30.0):
        """
        Initialize the API client.

        Args:
            base_url: Base URL for the API. Defaults to production if not provided.
            timeout: Request timeout in seconds
        """
        self.base_url = resolve_base_url(base_url)
        self.timeout = timeout
        self._api_client: ApiClient | None = None
        self._api: AsyncIgvfCatalogApi | None = None

    @property
    def api(self) -> AsyncIgvfCatalogApi:
        """The generated API instance, created on first use."""
        if self._api is None:
            self._api_client = ApiClient(Configuration(host=self.base_url))
            self._api = AsyncIgvfCatalogApi(self._api_client)
        return self._api

    async def close(self) -> None:
        """Close the underlying HTTP session."""
        if self._api_client is not None:
            await self._api_client.close()
        self._api_client = None
        self._api = None

    async def call(self, method_name: str, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Call a generated API method and return the JSON response as a list of dicts.

        The raw JSON is used instead of the generated response models so that every
        field the API returns is passed through unchanged.

        Args:
            method_name: AsyncIgvfCatalogApi method name (e.g., "genes", "genes_from_variants")
            **kwargs: Query parameters, using the generated method's keyword names. None values are dropped.

        Returns:
            List of result objects. A single object response is wrapped in a list.

        Raises:
            ValueError: If the method does not exist
            ApiException: If the API returns a non-2xx response
        """
        method_params(method_name)
        method = getattr(self.api, f'{method_name}_without_preload_content')

        params = {k: v for k, v in kwargs.items() if v is not None}
        response = RESTResponse(await method(**params, _request_timeout=self.timeout))
        body = await response.read()

        if not 200 <= response.status <= 299:
            try:
                ApiException.from_response(
                    http_resp=response,
                    body=body.decode('utf-8', errors='replace') if body else None,
                    data=None,
                )
            except ApiException as error:
                # Response headers only add noise to the error text returned to the LLM
                error.headers = None
                raise

        result = json.loads(body) if body else []
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return [result]
        return []

    async def call_all(self, method_name: str, page_size: int, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Call a paginated API method for every page and return all results.

        Args:
            method_name: AsyncIgvfCatalogApi method name
            page_size: Results per full page. Sent as the limit if the method accepts one, otherwise it must be
                the API's default page size.
            **kwargs: Query parameters other than page and limit

        Returns:
            Results of all pages, fetched until a page has fewer than page_size results
        """
        if 'limit' in method_params(method_name):
            kwargs['limit'] = page_size
        results: list[dict[str, Any]] = []
        page = 0
        while True:
            rows = await self.call(method_name, **kwargs, page=page)
            results.extend(rows)
            if len(rows) < page_size:
                return results
            page += 1


_client: IGVFCatalogClient | None = None


def get_client() -> IGVFCatalogClient:
    """Get the process-wide API client, creating it on first use."""
    global _client
    if _client is None:
        _client = IGVFCatalogClient()
    return _client


async def close_client() -> None:
    """Close the process-wide API client, if one was created."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None
