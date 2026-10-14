"""Tests for API client."""

from unittest.mock import AsyncMock, patch

import pytest
from igvf_catalog_async_client import AsyncIgvfCatalogApi
from igvf_catalog_async_client.exceptions import ApiException

from igvf_catalog_mcp.services import api_client
from igvf_catalog_mcp.services.api_client import IGVFCatalogClient, method_params, resolve_base_url
from tests.fakes import FakeResponse


def test_client_initialization(monkeypatch):
    """Test client initialization with default URL."""
    monkeypatch.delenv('IGVF_CATALOG_API_URL', raising=False)
    client = IGVFCatalogClient()
    assert client.base_url == 'https://api.catalogkg.igvf.org/api'
    assert client.timeout == 30.0


def test_client_env_url(monkeypatch):
    """Test that IGVF_CATALOG_API_URL overrides the default URL."""
    monkeypatch.setenv('IGVF_CATALOG_API_URL', 'https://catalog-api-dev.demo.igvf.org')
    assert IGVFCatalogClient().base_url == 'https://catalog-api-dev.demo.igvf.org/api'


def test_client_custom_url():
    """Test client initialization with custom URL."""
    client = IGVFCatalogClient(base_url='http://localhost:2023')
    assert client.base_url == 'http://localhost:2023/api'


@pytest.mark.parametrize(
    'url',
    ['http://localhost:2023/', 'http://localhost:2023/api', 'http://localhost:2023/api/'],
)
def test_resolve_base_url_appends_api_once(url):
    """Test that /api is appended exactly once and trailing slashes are stripped."""
    assert resolve_base_url(url) == 'http://localhost:2023/api'


def test_api_is_created_lazily_with_base_url():
    """Test the generated API instance is created on first use and reused."""
    client = IGVFCatalogClient(base_url='http://localhost:2023')
    assert client._api is None
    api = client.api
    assert isinstance(api, AsyncIgvfCatalogApi)
    assert api.api_client.configuration.host == 'http://localhost:2023/api'
    assert client.api is api


def test_method_params():
    """Test that method_params reads keyword names from the generated method."""
    params = method_params('genes')
    assert {'gene_id', 'name', 'region', 'page', 'limit'} <= params
    assert 'self' not in params
    assert not any(p.startswith('_') for p in params)


def test_method_params_unknown_method():
    """Test that unknown methods raise ValueError."""
    with pytest.raises(ValueError, match='Unknown IGVF Catalog API method'):
        method_params('not_a_method')


async def test_call_returns_list_and_drops_none():
    """Test call() invokes the generated method and returns parsed JSON."""
    client = IGVFCatalogClient(base_url='http://localhost:2023')
    mock = AsyncMock(return_value=FakeResponse([{'_id': 'ENSG00000139618'}]))
    with patch.object(client.api, 'genes_without_preload_content', mock):
        result = await client.call('genes', gene_id='ENSG00000139618', name=None, page=0)

    assert result == [{'_id': 'ENSG00000139618'}]
    mock.assert_awaited_once_with(gene_id='ENSG00000139618', page=0, _request_timeout=30.0)


async def test_call_wraps_single_object():
    """Test that a single object response is normalized into a list."""
    client = IGVFCatalogClient(base_url='http://localhost:2023')
    mock = AsyncMock(return_value=FakeResponse({'_id': 'R-HSA-164843'}))
    with patch.object(client.api, 'pathways_without_preload_content', mock):
        assert await client.call('pathways', id='R-HSA-164843') == [{'_id': 'R-HSA-164843'}]


async def test_call_raises_on_http_error():
    """Test that non-2xx responses raise ApiException."""
    client = IGVFCatalogClient(base_url='http://localhost:2023')
    mock = AsyncMock(return_value=FakeResponse({'message': 'bad'}, status=400, reason='Bad Request'))
    with patch.object(client.api, 'genes_without_preload_content', mock):
        with pytest.raises(ApiException) as excinfo:
            await client.call('genes', gene_id='x')
    assert excinfo.value.status == 400
    assert 'bad' in excinfo.value.body


async def test_call_rejects_unknown_kwargs():
    """Test that the generated method rejects parameters it does not define."""
    client = IGVFCatalogClient(base_url='http://localhost:2023')
    with pytest.raises(Exception, match='not_a_param'):
        await client.call('genes', not_a_param='x')


async def test_call_unknown_method():
    """Test that call() raises ValueError for unknown methods."""
    client = IGVFCatalogClient(base_url='http://localhost:2023')
    with pytest.raises(ValueError, match='Unknown IGVF Catalog API method'):
        await client.call('not_a_method')


async def test_call_all_fetches_until_short_page():
    client = IGVFCatalogClient(base_url='http://catalog.test')
    pages = {0: [{'i': 0}, {'i': 1}], 1: [{'i': 2}, {'i': 3}], 2: [{'i': 4}]}
    client.call = AsyncMock(side_effect=lambda method_name, page, **kwargs: pages[page])

    results = await client.call_all('variants', 2, rsid='rs1')

    assert results == [{'i': i} for i in range(5)]
    assert [c.kwargs for c in client.call.call_args_list] == [
        {'rsid': 'rs1', 'limit': 2, 'page': page} for page in range(3)
    ]


async def test_call_all_without_limit_parameter():
    client = IGVFCatalogClient(base_url='http://catalog.test')
    client.call = AsyncMock(return_value=[{'i': 0}])

    assert await client.call_all('complexes', 25, name='x') == [{'i': 0}]
    client.call.assert_awaited_once_with('complexes', name='x', page=0)


async def test_get_client_is_shared_and_closable(monkeypatch):
    """Test the process-wide client is created once and reset on close."""
    monkeypatch.setattr(api_client, '_client', None)
    first = api_client.get_client()
    assert api_client.get_client() is first
    await api_client.close_client()
    assert api_client._client is None
    assert api_client.get_client() is not first
    await api_client.close_client()
