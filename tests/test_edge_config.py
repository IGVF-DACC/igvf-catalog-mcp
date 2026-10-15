"""Tests for edge configuration system."""

import math

import pytest

from igvf_catalog_mcp.services.edge_config import (
    EDGE_ENDPOINTS,
    RELATIONSHIP_TYPE_MAPPING,
    get_all_sources,
    get_edge_config,
    get_endpoints_for_entity_and_relationship,
    get_sources_by_category,
    supports_verbose,
)
from igvf_catalog_mcp.tools.find_associations import build_query_params


def test_all_endpoints_have_required_fields():
    """Verify all endpoints have required configuration fields."""
    required_fields = ['client_method', 'path', 'from_type', 'max_limit']

    for endpoint_key, config in EDGE_ENDPOINTS.items():
        for field in required_fields:
            assert field in config, f'Endpoint {endpoint_key} missing field: {field}'


def test_endpoint_paths_are_unique():
    """Verify all endpoint paths are unique."""
    paths = [config['path'] for config in EDGE_ENDPOINTS.values()]
    assert len(paths) == len(set(paths)), 'Duplicate endpoint paths found'


def test_client_methods_are_unique():
    """Verify all endpoint client methods are unique."""
    methods = [config['client_method'] for config in EDGE_ENDPOINTS.values()]
    assert len(methods) == len(set(methods)), 'Duplicate client methods found'


def test_bidirectional_endpoints_exist():
    """Verify bidirectional endpoints are properly configured."""
    bidirectional_pairs = [
        ('variants_genes', 'genes_variants'),
        ('variants_proteins', 'proteins_variants'),
        ('variants_drugs', 'drugs_variants'),
        ('genes_diseases', 'diseases_genes'),
        ('genes_transcripts', 'transcripts_genes'),
        ('transcripts_proteins', 'proteins_transcripts'),
        ('complexes_proteins', 'proteins_complexes'),
        ('motifs_proteins', 'proteins_motifs'),
    ]

    for pair in bidirectional_pairs:
        assert pair[0] in EDGE_ENDPOINTS, f'Missing endpoint: {pair[0]}'
        assert pair[1] in EDGE_ENDPOINTS, f'Missing endpoint: {pair[1]}'


def test_sources_are_lists():
    """Verify sources field contains lists of strings."""
    for endpoint_key, config in EDGE_ENDPOINTS.items():
        if 'sources' in config:
            assert isinstance(
                config['sources'], list
            ), f'Endpoint {endpoint_key} sources should be a list'
            assert all(
                isinstance(s, str) for s in config['sources']
            ), f'Endpoint {endpoint_key} sources should contain strings'


def test_max_limits_are_reasonable():
    """Verify max_limit values are reasonable."""
    for endpoint_key, config in EDGE_ENDPOINTS.items():
        max_limit = config.get('max_limit', 100)
        assert 25 <= max_limit <= 1000, f'Endpoint {endpoint_key} has unreasonable max_limit: {max_limit}'


def test_get_existing_endpoint():
    """Test retrieving configuration for an existing endpoint."""
    config = get_edge_config('variants_genes')
    assert config is not None
    assert config['client_method'] == 'genes_from_variants'
    assert config['path'] == '/variants/genes'
    assert config['from_type'] == 'variant'
    assert config['to_type'] == 'gene'


def test_get_nonexistent_endpoint():
    """Test retrieving configuration for a non-existent endpoint."""
    config = get_edge_config('nonexistent_endpoint')
    assert config is None


def test_variants_genes_has_correct_sources():
    """Test variants_genes endpoint has correct source values."""
    config = get_edge_config('variants_genes')
    assert 'AFGR' in config['sources']
    assert 'EBI' in config['sources']
    assert 'IGVF' in config['sources']
    # Old incorrect values should not be present
    assert 'GTEx' not in config.get('sources', [])
    assert 'EBI eQTL Catalogue' not in config.get('sources', [])


def test_variants_proteins_has_correct_sources():
    """Test variants_proteins endpoint has correct source values."""
    config = get_edge_config('variants_proteins')
    assert 'ADASTRA' in config['sources']
    assert 'GVATdb' in config['sources']
    assert 'UKB' in config['sources']
    assert 'SEMVAR' in config['methods']


def test_variants_phenotypes_has_correct_methods():
    """Test variants_phenotypes endpoint has correct method values."""
    config = get_edge_config('variants_phenotypes')
    assert 'methods' in config
    assert 'cV2F' in config['methods']
    assert 'SGE' in config['methods']


def test_variants_variants_has_correct_path():
    """Test variants_variants endpoint uses the correct LD API path."""
    config = get_edge_config('variants_variants')
    assert config['client_method'] == 'variants_from_variant_id'
    assert config['path'] == '/variants/variant-ld'
    assert 'chr' not in config['from_params']
    assert 'position' not in config['from_params']


def test_go_terms_uses_gene_products_path():
    """Test GO term annotations use the gene-products endpoint."""
    config = get_edge_config('go_terms_annotations')
    assert config['client_method'] == 'go_terms_from_annotations'
    assert config['path'] == '/gene-products/go-terms'
    assert config['from_params'] == ['query']


def test_supports_verbose_is_derived_from_client():
    """Test verbose support comes from the generated method signature."""
    assert supports_verbose(get_edge_config('variants_genes'))
    assert not supports_verbose(get_edge_config('variants_coding_variants'))
    assert not supports_verbose(get_edge_config('go_terms_annotations'))


def test_all_relationship_types_defined():
    """Verify all expected relationship types are defined."""
    expected_types = [
        'regulatory',
        'genetic',
        'physical',
        'functional',
        'pharmacological',
        'ld',
        'coding',
        'transcription',
    ]

    for rel_type in expected_types:
        assert (
            rel_type in RELATIONSHIP_TYPE_MAPPING
        ), f'Missing relationship type: {rel_type}'


def test_get_endpoints_for_variant_regulatory():
    """Test getting regulatory endpoints for variants."""
    endpoints = get_endpoints_for_entity_and_relationship(
        'variant', 'regulatory')
    assert 'variants_genes' in endpoints
    assert 'variants_genomic_elements' in endpoints


def test_get_endpoints_for_gene_regulatory():
    """Test getting regulatory endpoints for genes."""
    endpoints = get_endpoints_for_entity_and_relationship(
        'gene', 'regulatory')
    assert 'genes_variants' in endpoints
    assert 'genes_genomic_elements' in endpoints


def test_get_endpoints_for_variant_ld():
    """Test getting LD endpoints for variants."""
    endpoints = get_endpoints_for_entity_and_relationship('variant', 'ld')
    assert 'variants_variants' in endpoints


def test_get_endpoints_for_protein_physical():
    """Test getting physical interaction endpoints for proteins."""
    endpoints = get_endpoints_for_entity_and_relationship(
        'protein', 'physical')
    assert 'proteins_proteins' in endpoints
    assert 'proteins_complexes' in endpoints


def test_get_endpoints_for_invalid_relationship():
    """Test getting endpoints for an invalid relationship type."""
    endpoints = get_endpoints_for_entity_and_relationship(
        'gene', 'invalid_relationship')
    assert endpoints == []


def test_get_endpoints_for_invalid_entity_type():
    """Test getting endpoints when entity type doesn't match relationship."""
    endpoints = get_endpoints_for_entity_and_relationship('gene', 'ld')
    assert endpoints == []


def test_get_all_sources_returns_unique_sources():
    """Test that get_all_sources returns unique source names."""
    sources = get_all_sources()
    assert isinstance(sources, set)
    assert len(sources) > 0

    # Check for known sources
    expected_sources = {'AFGR', 'EBI',
                        'ADASTRA', 'GVATdb', 'PharmGKB', 'Orphanet'}
    for source in expected_sources:
        assert source in sources, f'Expected source {source} not found'


def test_get_sources_by_category_structure():
    """Test that get_sources_by_category returns proper structure."""
    sources_by_cat = get_sources_by_category()
    assert isinstance(sources_by_cat, dict)

    expected_categories = [
        'variant_annotations',
        'gene_expression',
        'regulatory',
        'disease',
        'drugs',
        'interactions',
    ]

    for category in expected_categories:
        assert category in sources_by_cat, f'Missing category: {category}'
        assert isinstance(sources_by_cat[category], list)


def test_gene_expression_category_sources():
    """Test gene expression category has correct sources."""
    sources_by_cat = get_sources_by_category()
    gene_exp_sources = sources_by_cat['gene_expression']

    assert 'AFGR' in gene_exp_sources
    assert 'EBI' in gene_exp_sources
    assert 'IGVF' in gene_exp_sources


def test_regulatory_category_sources():
    """Test regulatory category has correct sources."""
    sources_by_cat = get_sources_by_category()
    reg_sources = sources_by_cat['regulatory']

    assert 'ADASTRA' in reg_sources
    assert 'GVATdb' in reg_sources
    assert 'ENCODE' in reg_sources


def test_variants_genes_filters():
    """Test variants_genes endpoint has correct filter configuration."""
    config = get_edge_config('variants_genes')
    filters = config.get('filters', {})

    assert 'neg_log10_pvalue' in filters
    assert filters['neg_log10_pvalue'] == 'range'
    assert 'log10pvalue' not in filters
    assert 'effect_size' in filters
    assert filters['effect_size'] == 'range'
    assert 'biological_context' in filters
    assert filters['biological_context'] == 'string'


def test_variants_variants_ld_filters():
    """Test variants_variants endpoint has LD-specific filters."""
    config = get_edge_config('variants_variants')
    filters = config.get('filters', {})

    assert 'r2' in filters
    assert filters['r2'] == 'range'
    assert 'd_prime' in filters
    assert filters['d_prime'] == 'range'
    assert 'ancestry' in filters
    assert filters['ancestry'] == 'enum'


def test_variants_drugs_filters():
    """Test variants_drugs endpoint has appropriate filters."""
    config = get_edge_config('variants_drugs')
    filters = config.get('filters', {})

    assert 'pmid' in filters
    assert 'phenotype_categories' in filters
    assert 'GENCODE_category' not in filters


def test_variants_genes_from_params():
    """Test variants_genes has correct from_params."""
    config = get_edge_config('variants_genes')
    from_params = config.get('from_params', [])

    assert 'variant_id' in from_params
    assert 'spdi' in from_params
    assert 'hgvs' in from_params
    assert 'rsid' in from_params
    assert 'ca_id' in from_params


def test_genes_variants_from_params():
    """Test genes_variants has correct from_params."""
    config = get_edge_config('genes_variants')
    from_params = config.get('from_params', [])

    assert 'gene_id' in from_params
    assert 'gene_name' in from_params
    assert 'hgnc_id' in from_params
    assert 'synonym' in from_params
    assert 'alias' not in from_params


def test_proteins_variants_from_params():
    """Test proteins_variants has correct from_params."""
    config = get_edge_config('proteins_variants')
    from_params = config.get('from_params', [])

    assert 'protein_id' in from_params
    assert 'protein_name' in from_params
    assert 'uniprot_full_name' in from_params
    assert 'full_name' not in from_params
    assert 'dbxrefs' in from_params


def test_value_list_filter_without_enum_is_passed_through():
    config = {**EDGE_ENDPOINTS['genes_genes']}
    del config['methods']

    params, not_applied = build_query_params('ENSG1', 'gene_id', config, {'method': 'anything'}, 25, False)

    assert params['method'] == 'anything'
    assert not not_applied


def test_malformed_range_filter_is_not_applied():
    config = EDGE_ENDPOINTS['genes_genomic_elements']

    params, not_applied = build_query_params('ENSG1', 'gene_id', config, {'score': 'above:0.5'}, 25, False)

    assert 'score' not in params
    assert not_applied['score'].startswith('invalid value; must be a number or an operator string')


def test_numeric_string_range_filter_is_a_minimum():
    params, not_applied = build_query_params(
        'ENSG1', 'gene_id', EDGE_ENDPOINTS['genes_genomic_elements'], {'score': '0.5'}, 25, False
    )

    assert params['score'] == 'gte:0.5'
    assert not not_applied


def test_number_is_an_exact_value_of_other_range_filters():
    params, not_applied = build_query_params(
        'ENSG1', 'gene_id', EDGE_ENDPOINTS['genes_variants'], {'effect_size': 2, 'neg_log10_pvalue': 'gte:5'}, 25, False
    )

    assert (params['effect_size'], params['neg_log10_pvalue']) == ('2', 'gte:5')
    assert not not_applied


@pytest.mark.parametrize(
    ('p_value', 'minimum'),
    [(0.05, 'gte:1.3010299956639813'), (0.01, 'gte:2.0'), (5e-8, 'gte:7.301029995663981'), (1e-5, 'gte:5.0'),
     (0.0002, 'gte:3.6989700043360187'), (2.5e-6, 'gte:5.6020599913279625'), (1e-300, 'gte:300.0')],
)
def test_p_value_is_sent_as_neg_log10_at_full_precision(p_value, minimum):
    params, not_applied = build_query_params(
        'ENSG1', 'gene_id', EDGE_ENDPOINTS['genes_variants'], {'p_value': p_value}, 25, False
    )

    assert params['neg_log10_pvalue'] == minimum
    assert not not_applied


def p_value_samples():
    return [mantissa / 100 * 10**-exponent for exponent in range(1, 300, 7) for mantissa in range(100, 1000, 3)]


def neg_log10_minimum(p_value):
    config = EDGE_ENDPOINTS['genes_variants']
    params, _ = build_query_params('ENSG1', 'gene_id', config, {'p_value': p_value}, 25, False)
    operator, value = params['neg_log10_pvalue'].split(':')
    assert operator == 'gte'
    return float(value)


def test_p_value_minimum_round_trips_to_the_p_value():
    for p_value in p_value_samples():
        minimum = neg_log10_minimum(p_value)
        assert minimum == -math.log10(p_value), p_value
        assert math.isclose(10**-minimum, p_value, rel_tol=1e-12), p_value


def test_p_value_minimum_admits_exactly_the_rows_within_the_maximum():
    for p_value in p_value_samples():
        minimum = neg_log10_minimum(p_value)
        for row_p_value in [p_value * (1 - 1e-9), p_value, p_value * (1 + 1e-9)]:
            assert (-math.log10(row_p_value) >= minimum) == (row_p_value <= p_value), (p_value, row_p_value)
