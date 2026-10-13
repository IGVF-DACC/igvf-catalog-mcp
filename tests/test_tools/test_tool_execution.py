"""Run each MCP tool through the server's call_tool with the catalog API mocked offline."""

import json

import pytest

from igvf_catalog_mcp.server import call_tool


def response_json(result):
    assert len(result) == 1
    return json.loads(result[0].text)


# get_entity


async def test_get_entity_gene_symbol(fake_catalog, sample_gene_data):
    fake_catalog.add('/genes', [sample_gene_data])

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': 'brca2'}))

    assert data == [{'_type': 'gene', **sample_gene_data}]
    assert fake_catalog.params_for('/genes') == [{'name': 'BRCA2', 'page': '0'}]


async def test_get_entity_pathway_uses_id(fake_catalog):
    fake_catalog.add('/pathways', {'_id': 'R-HSA-164843', 'name': '2-LTR circle formation'})

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': 'R-HSA-164843'}))

    assert data[0]['_type'] == 'pathway'
    assert data[0]['_id'] == 'R-HSA-164843'
    assert fake_catalog.params_for('/pathways') == [{'id': 'R-HSA-164843', 'page': '0'}]


async def test_get_entity_ontology_term(fake_catalog):
    fake_catalog.add('/ontology-terms', [{'term_id': 'MONDO_0008199', 'name': 'hereditary breast carcinoma'}])

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': 'MONDO:0008199'}))

    assert data[0]['_type'] == 'ontology'
    assert fake_catalog.params_for('/ontology-terms') == [{'term_id': 'MONDO_0008199', 'page': '0'}]


async def test_get_entity_not_found(fake_catalog):
    result = await call_tool('igvf_catalog_get_entity', {'id': 'ENSG00000000001'})

    assert result[0].text == "No gene found with gene_id='ENSG00000000001'"


async def test_get_entity_api_error(fake_catalog):
    fake_catalog.add('/genes', {'message': 'Internal error'}, status=500)

    result = await call_tool('igvf_catalog_get_entity', {'id': 'ENSG00000139618'})

    assert result[0].text.startswith('Error retrieving entity: ServiceException')
    assert 'Internal error' in result[0].text
    assert 'HTTP response headers' not in result[0].text


# search_region


async def test_search_region(fake_catalog, sample_gene_data, sample_variant_data):
    fake_catalog.add('/genes', [sample_gene_data, sample_gene_data])
    fake_catalog.add('/variants', [sample_variant_data])
    fake_catalog.add('/genomic-elements', [])

    data = response_json(
        await call_tool('igvf_catalog_search_region', {'region': '17:41M-42M', 'limit': 2, 'page': 1})
    )

    assert data['region'] == 'chr17:41000000-42000000'
    assert data['region_size_bp'] == 1_000_000
    assert data['results']['genes']['items'] == [sample_gene_data, sample_gene_data]
    assert data['results']['genes']['_pagination']['has_more'] is True
    assert data['results']['variants']['_pagination']['has_more'] is False
    assert data['results']['regulatory_elements']['items'] == []
    assert data['_pagination'] == {
        'current_page': 1,
        'limit': 2,
        'has_more': True,
        'next_page': 2,
        'note': 'More results available. Call again with page=2 to continue.',
    }
    expected_params = {'region': 'chr17:41000000-42000000', 'organism': 'Homo sapiens', 'limit': '2', 'page': '1'}
    for path in ['/genes', '/variants', '/genomic-elements']:
        assert fake_catalog.params_for(path) == [expected_params]


async def test_search_region_include_and_partial_error(fake_catalog):
    fake_catalog.add('/variants', {'message': 'region too large'}, status=400)

    data = response_json(
        await call_tool('igvf_catalog_search_region', {'region': 'chr1:1000-2000', 'include': ['genes', 'variants']})
    )

    assert set(data['results']) == {'genes', 'variants'}
    assert 'region too large' in data['results']['variants']['error']
    assert fake_catalog.params_for('/genomic-elements') == []


# find_associations


async def test_find_associations_variant_regulatory_filters(fake_catalog):
    fake_catalog.add('/variants/genes', [{'gene': 'genes/ENSG00000163874', 'log10pvalue': 12.0}])
    fake_catalog.add('/variants/genomic-elements', [{'genomic_element': 'genomic_elements/x'}])

    data = response_json(
        await call_tool(
            'igvf_catalog_find_associations',
            {
                'entity_id': 'rs58542926',
                'relationship': 'regulatory',
                'filters': {'p_value': 0.05, 'source': 'EBI', 'method': 'eQTL', 'biological_context': 'liver'},
                'verbose': True,
            },
        )
    )

    assert data['entity_type'] == 'variant'
    assert data['num_associations'] == 2
    assert [a['_endpoint'] for a in data['associations']] == ['variants_genes', 'variants_genomic_elements']
    assert [a['_endpoint_path'] for a in data['associations']] == ['/variants/genes', '/variants/genomic-elements']

    assert fake_catalog.params_for('/variants/genes') == [
        {
            'rsid': 'rs58542926',
            'neg_log10_pvalue': 'gte:1.30',
            'biological_context': 'liver',
            'method': 'eQTL',
            'source': 'EBI',
            'verbose': 'true',
            'page': '0',
            'limit': '25',
        }
    ]
    assert fake_catalog.params_for('/variants/genomic-elements') == [
        {'rsid': 'rs58542926', 'biological_context': 'liver', 'page': '0', 'limit': '25'}
    ]


async def test_find_associations_gene_symbol(fake_catalog):
    fake_catalog.add('/genes/variants', [{'variant': 'variants/x'}])

    data = response_json(
        await call_tool('igvf_catalog_find_associations', {'entity_id': 'ZC3H12A', 'relationship': 'regulatory'})
    )

    assert fake_catalog.params_for('/genes/variants') == [{'gene_name': 'ZC3H12A', 'page': '0', 'limit': '25'}]
    metadata = {m['endpoint']: m for m in data['query_metadata']}
    assert metadata['genes_variants']['results_count'] == 1
    assert 'not supported' in metadata['genomic_elements_genes']['error']
    assert fake_catalog.params_for('/genomic-elements/genes') == []


async def test_find_associations_protein_go_terms(fake_catalog):
    fake_catalog.add('/gene-products/go-terms', [{'go_term_name': 'DNA repair'}])

    data = response_json(
        await call_tool('igvf_catalog_find_associations', {'entity_id': 'P49711', 'relationship': 'functional'})
    )

    assert data['associations'][0]['_endpoint'] == 'go_terms_annotations'
    assert fake_catalog.params_for('/gene-products/go-terms') == [{'query': 'P49711', 'page': '0', 'limit': '25'}]


async def test_find_associations_ontology_term(fake_catalog):
    fake_catalog.add('/phenotypes/variants', [{'variant': 'variants/x'}])

    await call_tool('igvf_catalog_find_associations', {'entity_id': 'EFO_0004611', 'relationship': 'genetic'})

    assert fake_catalog.params_for('/phenotypes/variants') == [
        {'phenotype_id': 'EFO_0004611', 'page': '0', 'limit': '25'}
    ]
    assert fake_catalog.params_for('/diseases/genes') == [{'disease_id': 'EFO_0004611', 'page': '0', 'limit': '25'}]


async def test_find_associations_truncates_and_paginates(fake_catalog):
    fake_catalog.add('/genes/genes', [{'i': i} for i in range(3)])
    fake_catalog.add('/genes/pathways', [{'i': i} for i in range(3)])

    data = response_json(
        await call_tool(
            'igvf_catalog_find_associations',
            {'entity_id': 'ENSG00000163874', 'relationship': 'all', 'limit': 3, 'page': 2},
        )
    )

    assert data['num_associations'] == 6
    assert len(data['associations']) == 3
    assert data['_pagination']['has_more'] is True
    assert data['_pagination']['next_page'] == 3
    assert data['_pagination']['results_returned'] == 3
    assert fake_catalog.params_for('/genes/genes') == [{'gene_id': 'ENSG00000163874', 'page': '2', 'limit': '3'}]


async def test_find_associations_endpoint_error_is_reported(fake_catalog):
    fake_catalog.add('/genes/genes', {'message': 'boom'}, status=500)

    data = response_json(
        await call_tool('igvf_catalog_find_associations', {'entity_id': 'ENSG00000163874', 'relationship': 'physical'})
    )

    assert data['num_associations'] == 0
    assert 'boom' in data['query_metadata'][0]['error']


async def test_find_associations_unknown_relationship(fake_catalog):
    result = await call_tool('igvf_catalog_find_associations', {'entity_id': 'rs1', 'relationship': 'nope'})

    assert result[0].text.startswith('Unknown relationship type: nope')
    assert fake_catalog.requests == []


# find_ld


async def test_find_ld(fake_catalog):
    fake_catalog.add(
        '/variants/variant-ld',
        [{'r2': 0.9, 'd_prime': 1.0}, {'r2': 0.6, 'd_prime': 0.9}, {'r2': 0.3, 'd_prime': 0.5}],
    )

    data = response_json(
        await call_tool(
            'igvf_catalog_find_ld',
            {'variant_id': 'rs58542926', 'r2_threshold': 0.2, 'd_prime_threshold': 0.4, 'ancestry': 'AFR',
             'limit': 3, 'verbose': True},
        )
    )

    assert data['num_ld_variants'] == 3
    assert data['summary'] == {'strong_ld_count': 1, 'moderate_ld_count': 1, 'weak_ld_count': 1}
    assert data['_pagination']['has_more'] is True
    assert fake_catalog.params_for('/variants/variant-ld') == [
        {
            'rsid': 'rs58542926',
            'r2': 'gte:0.2',
            'd_prime': 'gte:0.4',
            'ancestry': 'AFR',
            'verbose': 'true',
            'page': '0',
            'limit': '3',
        }
    ]


async def test_find_ld_no_results(fake_catalog):
    data = response_json(await call_tool('igvf_catalog_find_ld', {'variant_id': 'NC_000019.10:19268739:C:A'}))

    assert data['num_ld_variants'] == 0
    assert data['param_used'] == 'spdi'
    assert 'No variants in LD found' in data['message']


async def test_find_ld_rejects_non_variant(fake_catalog):
    result = await call_tool('igvf_catalog_find_ld', {'variant_id': 'ENSG00000163874'})

    assert result[0].text.startswith('Error: Expected a variant ID, but got gene')
    assert fake_catalog.requests == []


# resolve_id


async def test_resolve_id_variant(fake_catalog, sample_variant_data):
    fake_catalog.add('/variants', [sample_variant_data])

    data = response_json(await call_tool('igvf_catalog_resolve_id', {'id': 'CA6028682'}))

    assert data['entity_type'] == 'variant'
    assert data['identifiers']['rsid'] == ['rs80357906']
    assert data['identifiers']['spdi'] == 'NC_000017.11:43044295:G:A'
    assert data['identifiers']['position'] == 43044295
    assert fake_catalog.params_for('/variants') == [{'ca_id': 'CA6028682', 'page': '0'}]


async def test_resolve_id_gene(fake_catalog, sample_gene_data):
    fake_catalog.add('/genes', [sample_gene_data])

    data = response_json(await call_tool('igvf_catalog_resolve_id', {'id': 'HGNC:1101'}))

    assert data['identifiers']['gene_id'] == 'ENSG00000139618'
    assert data['identifiers']['synonyms'] == ['FANCD1', 'BRCC2']
    assert fake_catalog.params_for('/genes') == [{'hgnc_id': 'HGNC:1101', 'page': '0'}]


# list_sources


async def test_list_sources_overview(fake_catalog):
    data = response_json(await call_tool('igvf_catalog_list_sources', {}))

    assert 'gene_expression' in data['categories']
    assert data['total_endpoints'] > 0
    assert fake_catalog.requests == []


async def test_list_sources_endpoint(fake_catalog):
    data = response_json(await call_tool('igvf_catalog_list_sources', {'endpoint': 'variants_genes'}))

    assert data['client_method'] == 'genes_from_variants'
    assert data['path'] == '/variants/genes'
    assert data['supports_verbose'] is True
    assert 'neg_log10_pvalue' in data['filters']


async def test_list_sources_unknown_category(fake_catalog):
    result = await call_tool('igvf_catalog_list_sources', {'category': 'nope'})

    assert result[0].text.startswith('Unknown category: nope')


async def test_unknown_tool():
    with pytest.raises(ValueError, match='Unknown tool'):
        await call_tool('igvf_catalog_nope', {})
