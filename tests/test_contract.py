"""Contract tests between the MCP configuration and the generated IGVF Catalog client.

These fail when the generated client (and so the catalog API spec) drops or renames a
method or parameter that the MCP server relies on, when the endpoint configuration
stops matching the OpenAPI spec shipped in the client, and when the client gains a
method that the MCP neither uses nor lists in UNUSED_CLIENT_METHODS.
"""

import inspect
import re

import pytest
from igvf_catalog_async_client import AsyncIgvfCatalogApi
from igvf_catalog_async_client import __version__ as client_version

from igvf_catalog_mcp.services.api_client import method_params
from igvf_catalog_mcp.services.catalog_spec import load_spec, max_page_size, operation, param_enum, param_schema
from igvf_catalog_mcp.services.edge_config import (
    DERIVED_KEYS,
    EDGE_ENDPOINT_DEFINITIONS,
    EDGE_ENDPOINTS,
    MAX_LIMIT_OVERRIDES,
    RELATIONSHIP_TYPE_MAPPING,
    SPEC_ENUM_KEYS,
)
from igvf_catalog_mcp.services.id_parser import (
    ENTITY_MAX_LIMITS,
    ENTITY_METHODS,
    MOUSE_FALLBACK_LOOKUPS,
    NAME_LOOKUP_PARAMS,
    NAME_PARAMS,
    ORGANISM_TYPES,
    IDParser,
)
from igvf_catalog_mcp.tools.find_associations import (
    EDGE_PARAM_ALIASES,
    RESOLVED_EDGE_PARAMS,
    build_query_params,
    resolve_edge_param,
)
from igvf_catalog_mcp.tools.search_region import REGION_QUERY_METHODS

PAGING_PARAMS = {'page', 'limit'}

# Client methods the MCP doesn't call, each with the reason. A client method that is neither called (see
# all_referenced_methods) nor listed here fails test_every_client_method_is_used_or_listed_as_unused, so a new catalog
# endpoint gets a decision: use it, or list it here.
UNUSED_CLIENT_METHODS: dict[str, str] = {
    # Edges that find_associations doesn't expose yet
    'annotations_from_go_terms': 'GO term -> gene product edge; only the gene product -> GO term side is exposed',
    'biosamples_from_variants': 'variant -> biosample STARR-seq/BlueSTARR/MPRA edge; not exposed yet',
    'coding_variants_from_phenotypes': 'phenotype -> coding variant edge; not exposed by find_associations yet',
    'genes_from_pathways': 'pathway -> gene edge; only the gene -> pathway side is exposed',
    'genes_from_proteins': 'protein -> gene edge; not exposed by find_associations yet',
    'genes_proteins_from_variants': 'variant -> genes and proteins edge; not exposed by find_associations yet',
    'genes_proteins_genes_proteins': 'gene/protein -> gene/protein edge; covered by genes_genes and proteins_proteins',
    'genes_transcripts_genes': 'MORF gene overexpression effects; not exposed by find_associations yet',
    'genomic_elements_from_genomic_elements': 'promoter perturbation effects on accessibility; not exposed yet',
    'genomic_elements_from_phenotypes': 'phenotype -> genomic element edge; not exposed by find_associations yet',
    'pathways_from_pathways': 'pathway -> pathway edge; not exposed by find_associations yet',
    'phenotypes_from_coding_variants': 'coding variant -> phenotype edge; not exposed by find_associations yet',
    'phenotypes_from_genomic_elements': 'genomic element -> phenotype edge; not exposed by find_associations yet',
    'proteins_from_genes': 'gene -> protein edge; not exposed by find_associations yet',
    'variants_from_biosamples': 'biosample -> variant STARR-seq/BlueSTARR/MPRA edge; not exposed yet',
    'variants_from_diseases': 'disease -> variant edge; not exposed by find_associations yet',
    'variants_from_gene_proteins': 'gene/protein -> variant edge; covered by genes_variants and proteins_variants',
    'variants_from_genomic_elements': 'genomic element -> variant edge; not exposed by find_associations yet',
    'variants_genomic_elements_genes': 'variant -> perturbed element -> gene; not exposed by find_associations yet',
    'coding_variants_from_genes': 'gene -> coding variant scores; not exposed by find_associations yet',
    'all_coding_variants_from_genes': 'all coding variant scores of a gene and dataset; not exposed yet',
    'predictions_from_variants': 'element-gene predictions of a variant; not exposed by find_associations yet',
    'genomic_elements_predictions_from_variant': 'predicted genes and cell types of a variant; not exposed yet',
    'enhancer_gene_predictions': 'element-gene pairs by genomic element; covered by genomic_elements_genes',
    'grn': 'gene regulatory network; not exposed yet',
    'nearest_genes': 'nearest genes of a region; not exposed yet',
    'qtls': 'QTLs by gene, variant or region; covered by variants_genes and genes_variants',
    # Ontology hierarchy
    'ontology_term_children': 'ontology hierarchy; not exposed yet',
    'ontology_term_parents': 'ontology hierarchy; not exposed yet',
    'ontology_term_transitive_closure': 'ontology hierarchy; not exposed yet',
    # Nodes that get_entity and search_region don't look up
    'coding_variants': 'coding variant nodes; not looked up by get_entity yet',
    'motifs': 'motif nodes; not looked up by get_entity yet',
    'files_filesets': 'dataset metadata, not a knowledge graph entity',
    'genes_structure': 'gene/transcript/protein structure (exons, UTRs); not exposed yet',
    'variants_alleles': 'gnomAD alleles in a region; not exposed yet',
    'variant_by_frequency_source': 'variants in a region by allele frequency; not exposed yet',
    # Summaries and counts
    'coding_variants_count_from_gene': 'count endpoint',
    'coding_variants_summary': 'summary endpoint',
    'deprecated_coding_variants_summary': 'deprecated summary endpoint',
    'genomic_elements_from_variants_count': 'count endpoint',
    'qtl_summary_endpoint': 'summary endpoint',
    'variant_summary': 'summary endpoint',
    'variants_from_variant_id_summary': 'summary endpoint; find_ld uses variants_from_variant_id',
    'variants_region_summary': 'summary endpoint',
    # Other
    'llm_query': 'password-protected natural language query endpoint',
}


def public_client_methods() -> set[str]:
    """Names of the generated client's API methods, without their _with_http_info and _without_preload_content forms."""
    return {
        name
        for name, member in inspect.getmembers(AsyncIgvfCatalogApi, inspect.isfunction)
        if not name.startswith('_') and not name.endswith(('_with_http_info', '_without_preload_content'))
    }


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


def test_every_client_method_is_used_or_listed_as_unused():
    unknown = public_client_methods() - all_referenced_methods() - set(UNUSED_CLIENT_METHODS)
    assert not unknown, (
        f'Client methods neither used by the MCP nor listed in UNUSED_CLIENT_METHODS: {sorted(unknown)}. '
        'Use them, or add them to UNUSED_CLIENT_METHODS with the reason.'
    )


def test_unused_client_methods_exist_and_are_unused():
    listed = set(UNUSED_CLIENT_METHODS)
    assert not listed - public_client_methods(), 'UNUSED_CLIENT_METHODS lists methods the client no longer has'
    assert not listed & all_referenced_methods(), 'UNUSED_CLIENT_METHODS lists methods the MCP uses'


def test_spec_version_matches_client():
    # The spec states the catalog API version: the client version without .postN
    assert load_spec()['info']['version'] == re.sub(r'\.post\d+$', '', client_version)


@pytest.mark.parametrize('method_name', sorted(public_client_methods()))
def test_spec_path_matches_client(method_name):
    # The shipped spec and the generated code describe the same API
    assert operation(method_name)[0] == resource_path(method_name)


@pytest.mark.parametrize('endpoint_key', sorted(EDGE_ENDPOINT_DEFINITIONS))
def test_definitions_set_no_derived_keys(endpoint_key):
    definition = EDGE_ENDPOINT_DEFINITIONS[endpoint_key]
    hand_written = DERIVED_KEYS & set(definition)
    if param_schema(definition['client_method'], 'source') is None:
        # Sources describe the endpoint's data where the API has no source parameter
        hand_written -= {'sources'}
    assert not hand_written, f'{endpoint_key}: {sorted(hand_written)} come from the spec'


@pytest.mark.parametrize('endpoint_key', sorted(MAX_LIMIT_OVERRIDES))
def test_max_limit_overrides_only_where_the_spec_has_none(endpoint_key):
    assert endpoint_key in EDGE_ENDPOINT_DEFINITIONS
    method_name = EDGE_ENDPOINT_DEFINITIONS[endpoint_key]['client_method']
    assert max_page_size(method_name) is None, f'{endpoint_key}: the spec now states a page size; drop the override'


@pytest.mark.parametrize('endpoint_key', sorted(EDGE_ENDPOINTS))
def test_edge_config_is_derived_from_spec(endpoint_key):
    config = EDGE_ENDPOINTS[endpoint_key]
    method_name = config['client_method']

    assert config['path'] == operation(method_name)[0]
    assert config['max_limit'] == (max_page_size(method_name) or MAX_LIMIT_OVERRIDES[endpoint_key])
    for key, param_name in SPEC_ENUM_KEYS.items():
        values = param_enum(method_name, param_name)
        if values is not None:
            assert config[key] == values
        elif key != 'sources':
            # Without an enum the value is passed through, so a list would reject valid values
            assert key not in config, f'{endpoint_key}: {param_name} has no enum in the spec'


@pytest.mark.parametrize('endpoint_key', sorted(EDGE_ENDPOINTS))
def test_enum_filters_are_enums_in_spec(endpoint_key):
    config = EDGE_ENDPOINTS[endpoint_key]
    for filter_name, kind in config.get('filters', {}).items():
        if kind == 'enum':
            assert param_enum(config['client_method'], filter_name), f'{endpoint_key}.{filter_name} has no enum'


@pytest.mark.parametrize('endpoint_key', sorted(EDGE_ENDPOINTS))
def test_edge_config_matches_client(endpoint_key):
    config = EDGE_ENDPOINTS[endpoint_key]
    accepted = method_params(config['client_method'])

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

    params, not_applied = build_query_params('x', config['from_params'][0], config, filters, 25, True, 0)

    assert set(params) <= accepted
    assert not set(config.get('filters', {})) & set(not_applied)


@pytest.mark.parametrize('endpoint_key', sorted(EDGE_ENDPOINTS))
def test_edge_organisms_match_client(endpoint_key):
    config = EDGE_ENDPOINTS[endpoint_key]
    assert ('organisms' in config) == ('organism' in method_params(config['client_method']))
    assert set(config.get('organisms', ['Homo sapiens'])) <= {'Homo sapiens', 'Mus musculus'}


def test_edge_param_aliases_are_used():
    from_params = {p for config in EDGE_ENDPOINTS.values() for p in config.get('from_params', [])}
    for aliases in EDGE_PARAM_ALIASES.values():
        assert set(aliases) <= from_params


def test_entity_lookup_params_match_client():
    for _, entity_type, param_name in IDParser.PATTERNS:
        method_name = IDParser.get_client_method(entity_type)
        assert param_name in method_params(method_name), f'{param_name} not accepted by {method_name}'
        assert 'page' in method_params(method_name)


@pytest.mark.parametrize('entity_type', ORGANISM_TYPES)
def test_organism_types_accept_organism(entity_type):
    assert 'organism' in method_params(IDParser.get_client_method(entity_type))


def test_mouse_fallback_lookups_take_organism():
    for entity_type, param_name in MOUSE_FALLBACK_LOOKUPS:
        assert entity_type in ORGANISM_TYPES
        assert param_name in method_params(IDParser.get_client_method(entity_type))


def test_name_lookup_params_match_client():
    for entity_type, param_name in NAME_PARAMS.items():
        method_name = IDParser.get_client_method(entity_type)
        assert param_name in method_params(method_name), f'{param_name} not accepted by {method_name}'


def test_name_lookup_params_cover_every_name_lookup():
    assert set(NAME_LOOKUP_PARAMS) == set(NAME_PARAMS)
    for entity_type, param_names in NAME_LOOKUP_PARAMS.items():
        assert NAME_PARAMS[entity_type] in param_names
        method_name = IDParser.get_client_method(entity_type)
        missing = set(param_names) - method_params(method_name)
        assert not missing, f'{sorted(missing)} not accepted by {method_name}'


def test_entity_max_limits_match_client():
    for entity_type, method_name in ENTITY_METHODS.items():
        assert ('limit' in method_params(method_name)) == (entity_type in ENTITY_MAX_LIMITS), method_name
        if entity_type in ENTITY_MAX_LIMITS:
            assert ENTITY_MAX_LIMITS[entity_type] == max_page_size(method_name)


def test_resolved_edge_params_match_client():
    for (entity_type, param_name), (resolved_param, _) in RESOLVED_EDGE_PARAMS.items():
        assert {param_name, 'page'} <= method_params(IDParser.get_client_method(entity_type))
        assert any(resolve_edge_param(resolved_param, config) for config in EDGE_ENDPOINTS.values())


@pytest.mark.parametrize(
    'entity_type', sorted({t for mapping in RELATIONSHIP_TYPE_MAPPING.values() for t in mapping} & set(NAME_PARAMS))
)
def test_names_resolve_to_a_parameter_of_every_endpoint(entity_type):
    resolved_param, _ = RESOLVED_EDGE_PARAMS[(entity_type, 'name')]
    for mapping in RELATIONSHIP_TYPE_MAPPING.values():
        for endpoint_key in mapping.get(entity_type, []):
            assert resolve_edge_param(resolved_param, EDGE_ENDPOINTS[endpoint_key]), endpoint_key
            assert resolve_edge_param('name', EDGE_ENDPOINTS[endpoint_key]) is None, endpoint_key


@pytest.mark.parametrize('method_name', sorted(set(REGION_QUERY_METHODS.values())))
def test_region_query_params_match_client(method_name):
    assert {'region', 'organism', 'limit', 'page'} <= method_params(method_name)


def test_ld_params_match_client():
    config = EDGE_ENDPOINTS['variants_variants']
    params = method_params(config['client_method'])
    assert {'rsid', 'spdi', 'hgvs', 'ca_id', 'r2', 'd_prime', 'ancestry', 'verbose', 'limit', 'page'} <= params

