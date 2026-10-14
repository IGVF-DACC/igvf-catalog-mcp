"""Contract tests between the MCP configuration and the generated IGVF Catalog client.

These fail when the generated client (and so the catalog API spec) drops or renames a
method or parameter that the MCP server relies on.
"""

import inspect
import json
import os
import re

import pytest
from igvf_catalog_async_client import AsyncIgvfCatalogApi

from igvf_catalog_mcp.services.api_client import method_params
from igvf_catalog_mcp.services.edge_config import EDGE_ENDPOINTS
from igvf_catalog_mcp.services.id_parser import ENTITY_MAX_LIMITS, ENTITY_METHODS, NAME_PARAMS, IDParser
from igvf_catalog_mcp.tools.find_associations import EDGE_PARAM_ALIASES, RESOLVED_EDGE_PARAMS, build_query_params
from igvf_catalog_mcp.tools.search_region import REGION_QUERY_METHODS

PAGING_PARAMS = {'page', 'limit'}


def resource_path(method_name: str) -> str:
    """Read the API path a generated method requests from its serializer."""
    source = inspect.getsource(getattr(AsyncIgvfCatalogApi, f'_{method_name}_serialize'))
    match = re.search(r"resource_path='([^']+)'", source)
    assert match, f'No resource_path found for {method_name}'
    return match.group(1)


def all_referenced_methods() -> set[str]:
    methods = {config['client_method'] for config in EDGE_ENDPOINTS.values()}
    methods.update(ENTITY_METHODS.values())
    methods.update(REGION_QUERY_METHODS.values())
    return methods


@pytest.mark.parametrize('method_name', sorted(all_referenced_methods()))
def test_method_exists(method_name):
    assert hasattr(AsyncIgvfCatalogApi, method_name)
    assert hasattr(AsyncIgvfCatalogApi, f'{method_name}_without_preload_content')


@pytest.mark.parametrize('endpoint_key', sorted(EDGE_ENDPOINTS))
def test_edge_config_matches_client(endpoint_key):
    config = EDGE_ENDPOINTS[endpoint_key]
    accepted = method_params(config['client_method'])

    assert resource_path(config['client_method']) == config['path']

    used = set(config.get('from_params', [])) | set(config.get('filters', {})) | PAGING_PARAMS
    missing = used - accepted
    assert not missing, f'{endpoint_key}: {sorted(missing)} not accepted by {config["client_method"]}'


@pytest.mark.parametrize('endpoint_key', sorted(EDGE_ENDPOINTS))
def test_build_query_params_emits_accepted_kwargs(endpoint_key):
    config = EDGE_ENDPOINTS[endpoint_key]
    accepted = method_params(config['client_method'])
    filters = {name: 'gte:0.5' if kind == 'range' else 'x' for name, kind in config.get('filters', {}).items()}
    filters['p_value'] = 0.05
    for filter_name, allowed_key in [('source', 'sources'), ('method', 'methods'), ('label', 'labels')]:
        if config.get(allowed_key):
            filters[filter_name] = config[allowed_key][0]

    params = build_query_params('x', config['from_params'][0], config, filters, 25, True, 0)

    assert set(params) <= accepted


def test_edge_param_aliases_are_used():
    from_params = {p for config in EDGE_ENDPOINTS.values() for p in config.get('from_params', [])}
    for aliases in EDGE_PARAM_ALIASES.values():
        assert set(aliases) <= from_params


def test_entity_lookup_params_match_client():
    for _, entity_type, param_name in IDParser.PATTERNS:
        method_name = IDParser.get_client_method(entity_type)
        assert param_name in method_params(method_name), f'{param_name} not accepted by {method_name}'
        assert 'page' in method_params(method_name)


def test_name_lookup_params_match_client():
    for entity_type, param_name in NAME_PARAMS.items():
        method_name = IDParser.get_client_method(entity_type)
        assert param_name in method_params(method_name), f'{param_name} not accepted by {method_name}'


def test_entity_max_limits_match_client():
    for entity_type, method_name in ENTITY_METHODS.items():
        assert ('limit' in method_params(method_name)) == (entity_type in ENTITY_MAX_LIMITS), method_name


def test_resolved_edge_params_match_client():
    for param_name, (edge_param, _) in RESOLVED_EDGE_PARAMS.items():
        entity_type = next(entity_type for _, entity_type, name in IDParser.PATTERNS if name == param_name)
        assert {param_name, 'limit', 'page'} <= method_params(IDParser.get_client_method(entity_type))
        assert any(edge_param in config.get('from_params', []) for config in EDGE_ENDPOINTS.values())


@pytest.mark.parametrize('method_name', sorted(set(REGION_QUERY_METHODS.values())))
def test_region_query_params_match_client(method_name):
    assert {'region', 'organism', 'limit', 'page'} <= method_params(method_name)


def test_ld_params_match_client():
    config = EDGE_ENDPOINTS['variants_variants']
    params = method_params(config['client_method'])
    assert {'rsid', 'spdi', 'hgvs', 'ca_id', 'r2', 'd_prime', 'ancestry', 'verbose', 'limit', 'page'} <= params


@pytest.mark.skipif(
    not os.getenv('IGVF_CATALOG_OPENAPI_SPEC'),
    reason='Set IGVF_CATALOG_OPENAPI_SPEC to a processed catalog OpenAPI spec to check enum values',
)
def test_edge_enum_values_match_spec():
    with open(os.environ['IGVF_CATALOG_OPENAPI_SPEC']) as f:
        spec = json.load(f)

    for endpoint_key, config in EDGE_ENDPOINTS.items():
        spec_params = {p['name']: p.get('schema', {}) for p in spec['paths'][config['path']]['get']['parameters']}
        for filter_name, allowed_key in [('source', 'sources'), ('method', 'methods'), ('label', 'labels')]:
            if filter_name in spec_params and allowed_key in config:
                spec_values = set(spec_params[filter_name].get('enum', []))
                unknown = set(config[allowed_key]) - spec_values
                assert not unknown, f'{endpoint_key}.{allowed_key}: {sorted(unknown)} not in spec enum'
        for filter_name, kind in config.get('filters', {}).items():
            if kind == 'enum':
                assert 'enum' in spec_params[filter_name], f'{endpoint_key}.{filter_name} is not an enum in the spec'
