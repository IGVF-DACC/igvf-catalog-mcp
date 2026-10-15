"""Run each MCP tool through the server's call_tool with the catalog API mocked offline."""

import json

import pytest
from mcp import types

from igvf_catalog_mcp.server import app, call_tool
from igvf_catalog_mcp.services.formatter import ToolError

BRCA1 = {'_id': 'ENSG00000012048', 'name': 'BRCA1'}


def response_json(result):
    assert len(result) == 1
    return json.loads(result[0].text)


# get_entity


async def test_get_entity_gene_symbol(fake_catalog, sample_gene_data):
    fake_catalog.add('/genes', [sample_gene_data])

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': 'brca2'}))

    assert data['entities'] == [{'_type': 'gene', **sample_gene_data}]
    assert fake_catalog.params_for('/genes') == [{'name': 'BRCA2', 'limit': '500', 'page': '0'}]


async def test_get_entity_gene_symbol_must_match_exactly(fake_catalog):
    fake_catalog.add('/genes', [{'_id': 'ENSG00000266304', 'name': 'LIVAR'}])

    result = await call_tool('igvf_catalog_get_entity', {'id': 'liver'})

    assert result[0].text == "No gene found with symbol 'LIVER'. Did you mean: LIVAR?"


async def test_get_entity_gene_hint_must_match_exactly(fake_catalog, sample_gene_data):
    fake_catalog.add('/genes', [sample_gene_data, BRCA1])

    result = await call_tool('igvf_catalog_get_entity', {'id': 'BRCA', 'hint': 'gene'})

    assert result[0].text == "No gene found with symbol 'BRCA'. Did you mean: BRCA2, BRCA1?"


async def test_get_entity_gene_symbol_returns_only_exact_matches(fake_catalog, sample_gene_data):
    fake_catalog.add('/genes', [sample_gene_data, BRCA1])

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': 'brca1'}))

    assert data['entities'] == [{'_type': 'gene', **BRCA1}]
    assert data['_pagination']['has_more'] is False


async def test_get_entity_pages_exact_gene_matches(fake_catalog):
    genes = [{'_id': f'ENSG0000000000{i}', 'name': 'PAR1'} for i in range(3)]
    fake_catalog.add('/genes', genes)

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': 'PAR1', 'limit': 2, 'page': 1}))

    assert [entity['_id'] for entity in data['entities']] == ['ENSG00000000002']
    assert data['_pagination']['has_more'] is False
    assert fake_catalog.params_for('/genes') == [{'name': 'PAR1', 'limit': '500', 'page': '0'}]


@pytest.mark.parametrize('symbol', ['RS1', 'CA1'])
async def test_get_entity_gene_symbol_shaped_like_variant_id(fake_catalog, symbol):
    fake_catalog.add('/genes', [{'_id': 'ENSG00000102104', 'name': symbol}])

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': symbol}))

    assert data['entity_type'] == 'gene'
    assert data['entities'][0]['name'] == symbol
    assert fake_catalog.params_for('/variants') == []


async def test_get_entity_variant_id_without_matching_gene(fake_catalog, sample_variant_data):
    fake_catalog.add('/variants', [sample_variant_data])

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': 'CA6028682'}))

    assert data['entity_type'] == 'variant'
    assert fake_catalog.params_for('/genes') == [{'name': 'CA6028682', 'limit': '500', 'page': '0'}]
    assert fake_catalog.params_for('/variants') == [{'ca_id': 'CA6028682', 'page': '0', 'limit': '25'}]


async def test_get_entity_pathway_uses_id(fake_catalog):
    fake_catalog.add('/pathways', {'_id': 'R-HSA-164843', 'name': '2-LTR circle formation'})

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': 'R-HSA-164843'}))

    assert data['entities'][0]['_type'] == 'pathway'
    assert data['entities'][0]['_id'] == 'R-HSA-164843'
    assert fake_catalog.params_for('/pathways') == [{'id': 'R-HSA-164843', 'page': '0', 'limit': '25'}]


async def test_get_entity_ontology_term(fake_catalog):
    fake_catalog.add('/ontology-terms', [{'term_id': 'MONDO_0008199', 'name': 'hereditary breast carcinoma'}])

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': 'MONDO:0008199'}))

    assert data['entities'][0]['_type'] == 'ontology'
    assert fake_catalog.params_for('/ontology-terms') == [{'term_id': 'MONDO_0008199', 'page': '0', 'limit': '25'}]


async def test_get_entity_generic_ontology_term(fake_catalog):
    fake_catalog.add('/ontology-terms', [{'term_id': 'HP_0033726', 'name': 'Systemic lupus erythematosus'}])

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': 'hp:0033726'}))

    assert data['entity_type'] == 'ontology'
    assert fake_catalog.params_for('/ontology-terms') == [{'term_id': 'HP_0033726', 'page': '0', 'limit': '25'}]


async def test_get_entity_uniprot_accession_uses_dbxrefs(fake_catalog):
    fake_catalog.add('/proteins', [{'_id': 'ENSP00000494538', 'names': ['CTCF_HUMAN']}])

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': 'P49711'}))

    assert data['entities'][0]['_type'] == 'protein'
    assert fake_catalog.params_for('/proteins') == [{'dbxrefs': 'P49711', 'page': '0', 'limit': '25'}]


async def test_get_entity_uniprot_isoform_uses_protein_id(fake_catalog):
    await call_tool('igvf_catalog_get_entity', {'id': 'P49711-1'})

    assert fake_catalog.params_for('/proteins') == [{'protein_id': 'P49711-1', 'page': '0', 'limit': '25'}]


async def test_get_entity_gene_symbol_resembling_accession(fake_catalog):
    fake_catalog.add('/genes', [{'_id': 'ENSG00000148737', 'name': 'TCF7L2'}])

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': 'TCF7L2'}))

    assert data['entities'][0]['_type'] == 'gene'
    assert fake_catalog.params_for('/genes') == [{'name': 'TCF7L2', 'limit': '500', 'page': '0'}]
    assert fake_catalog.params_for('/proteins') == []


async def test_get_entity_hint_looks_up_protein_by_name(fake_catalog):
    fake_catalog.add('/proteins', [{'_id': 'ENSP00000494538', 'name': 'CTCF'}])

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': 'CTCF', 'hint': 'protein'}))

    assert data['entities'][0]['_type'] == 'protein'
    assert fake_catalog.params_for('/proteins') == [{'name': 'CTCF', 'page': '0', 'limit': '25'}]
    assert fake_catalog.params_for('/genes') == []


async def test_get_entity_hint_looks_up_disease_by_name(fake_catalog):
    fake_catalog.add('/ontology-terms', [{'term_id': 'MONDO_0004670', 'name': 'lupus erythematosus'}])

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': 'lupus', 'hint': 'disease'}))

    assert data['entities'][0]['_type'] == 'ontology'
    assert fake_catalog.params_for('/ontology-terms') == [{'name': 'lupus', 'page': '0', 'limit': '25'}]


async def test_get_entity_paginates_name_lookups(fake_catalog):
    fake_catalog.add('/ontology-terms', [{'term_id': 'MONDO_0004670'}, {'term_id': 'MONDO_0019560'}])

    data = response_json(
        await call_tool('igvf_catalog_get_entity', {'id': 'lupus', 'hint': 'disease', 'limit': 2, 'page': 1})
    )

    assert len(data['entities']) == 2
    assert data['_pagination']['has_more'] is True
    assert data['_pagination']['next_page'] == 2
    assert fake_catalog.params_for('/ontology-terms') == [{'name': 'lupus', 'page': '1', 'limit': '2'}]


async def test_get_entity_reports_capped_limit(fake_catalog):
    await call_tool('igvf_catalog_get_entity', {'id': 'CTCF', 'hint': 'protein', 'limit': 200})
    result = await call_tool('igvf_catalog_get_entity', {'id': 'CPX-9', 'limit': 200})

    assert fake_catalog.params_for('/proteins') == [{'name': 'CTCF', 'page': '0', 'limit': '50'}]
    assert fake_catalog.params_for('/complexes') == [{'complex_id': 'CPX-9', 'page': '0'}]
    assert result[0].text == "No complex found with complex_id='CPX-9'"


async def test_get_entity_capped_limit_in_pagination(fake_catalog):
    fake_catalog.add('/complexes', [{'_id': 'CPX-9'}])

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': 'CPX-9', 'limit': 50}))

    assert data['_pagination']['limit'] == 50
    assert data['_pagination']['page_size'] == 25
    assert 'limit_capped_to' not in data['_pagination']
    assert data['_pagination']['has_more'] is False
    assert data['note'] == 'Complex lookups have a fixed page size of 25, so limit does not apply.'


async def test_get_entity_fixed_page_size_is_not_a_cap(fake_catalog):
    fake_catalog.add('/complexes', [{'_id': f'CPX-{i}'} for i in range(6)])

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': 'cohesin', 'hint': 'complex', 'limit': 5}))

    assert len(data['entities']) == 6
    assert data['_pagination']['limit'] == 5
    assert data['_pagination']['page_size'] == 25
    assert 'limit_capped_to' not in data['_pagination']
    assert fake_catalog.params_for('/complexes') == [{'name': 'cohesin', 'page': '0'}]


async def test_get_entity_reports_cap_below_request(fake_catalog):
    fake_catalog.add('/proteins', [{'_id': 'ENSP00000264010', 'name': 'CTCF'}])

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': 'CTCF', 'hint': 'protein', 'limit': 200}))
    assert data['_pagination']['limit_capped_to'] == 50
    assert 'note' not in data

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': 'CTCF', 'hint': 'protein', 'limit': 5}))
    assert 'limit_capped_to' not in data['_pagination']


async def test_get_entity_empty_later_page(fake_catalog):
    fake_catalog.add('/genes', [BRCA1])

    data = response_json(await call_tool('igvf_catalog_get_entity', {'id': 'BRCA1', 'page': 3}))

    assert data['entities'] == []
    assert data['_pagination']['has_more'] is False


async def test_get_entity_not_found(fake_catalog):
    result = await call_tool('igvf_catalog_get_entity', {'id': 'ENSG00000000001'})

    assert result[0].text == "No gene found with gene_id='ENSG00000000001'"


async def test_get_entity_api_error(fake_catalog):
    fake_catalog.add('/genes', {'message': 'Internal error'}, status=500)

    with pytest.raises(ToolError) as error:
        await call_tool('igvf_catalog_get_entity', {'id': 'ENSG00000139618'})

    assert str(error.value).startswith('Error retrieving entity: ServiceException')
    assert 'Internal error' in str(error.value)
    assert 'HTTP response headers' not in str(error.value)


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


async def test_find_associations_reports_filters_not_applied(fake_catalog):
    data = response_json(
        await call_tool(
            'igvf_catalog_find_associations',
            {
                'entity_id': 'ENSG00000163874',
                'relationship': 'regulatory',
                'filters': {'method': 'eQTL', 'source': 'EBI eQTL Catalogue', 'biological_context': 'liver'},
            },
        )
    )

    metadata = {m['endpoint']: m for m in data['query_metadata']}
    assert metadata['genes_variants']['filters_not_applied'] == {'source': 'invalid value; valid: AFGR, EBI, IGVF'}
    assert metadata['genes_genomic_elements']['filters_not_applied'] == {
        'method': 'invalid value; valid: CRISPR screen, ENCODE-rE2G, Perturb-seq, scE2G',
        'source': 'invalid value; valid: ENCODE, IGVF',
    }
    assert data['note'].startswith('Filters not applied to any endpoint: source.')
    assert fake_catalog.params_for('/genes/variants') == [
        {'gene_id': 'ENSG00000163874', 'biological_context': 'liver', 'method': 'eQTL', 'page': '0', 'limit': '25'}
    ]
    assert fake_catalog.params_for('/genes/genomic-elements') == [
        {'gene_id': 'ENSG00000163874', 'biological_context': 'liver', 'page': '0', 'limit': '25'}
    ]


async def test_find_associations_unsupported_filter(fake_catalog):
    data = response_json(
        await call_tool(
            'igvf_catalog_find_associations',
            {'entity_id': 'ENSG00000163874', 'relationship': 'functional', 'filters': {'p_value': 0.01, 'r2': 0.8}},
        )
    )

    assert data['query_metadata'][0]['filters_not_applied'] == {
        'p_value': 'not supported by this endpoint',
        'r2': 'not supported by this endpoint',
    }
    assert data['note'].startswith('Filters not applied to any endpoint: p_value, r2.')


async def test_find_associations_score_filter(fake_catalog):
    data = response_json(
        await call_tool(
            'igvf_catalog_find_associations',
            {'entity_id': 'ENSG00000012048', 'relationship': 'regulatory', 'filters': {'score': 0.7}},
        )
    )

    metadata = {m['endpoint']: m for m in data['query_metadata']}
    assert metadata['genes_genomic_elements']['params_used']['score'] == 'gte:0.7'
    assert 'filters_not_applied' not in metadata['genes_genomic_elements']
    assert metadata['genes_variants']['filters_not_applied'] == {'score': 'not supported by this endpoint'}
    assert 'note' not in data
    assert fake_catalog.params_for('/genes/genomic-elements')[0]['score'] == 'gte:0.7'
    assert 'score' not in fake_catalog.params_for('/genes/variants')[0]


async def test_find_associations_score_filter_with_operator(fake_catalog):
    await call_tool(
        'igvf_catalog_find_associations',
        {'entity_id': 'ENSG00000012048', 'relationship': 'regulatory', 'filters': {'score': 'gt:0.7'}},
    )

    assert fake_catalog.params_for('/genes/genomic-elements')[0]['score'] == 'gt:0.7'


async def test_find_associations_gene_symbol(fake_catalog):
    fake_catalog.add('/genes', [{'_id': 'ENSG00000163874', 'name': 'ZC3H12A'}, {'_id': 'ENSG1', 'name': 'ZC3H12AB'}])
    fake_catalog.add('/genes/variants', [{'variant': 'variants/x'}])
    fake_catalog.add('/genes/genomic-elements', [{'genomic_element': 'genomic_elements/x'}])

    data = response_json(
        await call_tool('igvf_catalog_find_associations', {'entity_id': 'zc3h12a', 'relationship': 'regulatory'})
    )

    assert data['resolved_entities'] == [{'id': 'ENSG00000163874', 'name': 'ZC3H12A'}]
    assert fake_catalog.params_for('/genes') == [{'name': 'ZC3H12A', 'limit': '500', 'page': '0'}]
    assert fake_catalog.params_for('/genes/variants') == [{'gene_id': 'ENSG00000163874', 'page': '0', 'limit': '25'}]
    metadata = {m['endpoint']: m for m in data['query_metadata']}
    assert metadata['genes_variants']['results_count'] == 1
    assert metadata['genes_variants']['resolved_from'] == 'name'
    assert metadata['genes_variants']['params_used']['gene_id'] == ['ENSG00000163874']
    assert metadata['genes_genomic_elements']['results_count'] == 1
    assert fake_catalog.params_for('/genes/genomic-elements') == [
        {'gene_id': 'ENSG00000163874', 'page': '0', 'limit': '25'}
    ]


async def test_find_associations_gene_symbol_without_exact_match(fake_catalog):
    fake_catalog.add('/genes', [{'_id': 'ENSG00000266304', 'name': 'LIVAR'}])

    result = await call_tool('igvf_catalog_find_associations', {'entity_id': 'liver', 'relationship': 'regulatory'})

    assert result[0].text == "No gene found with symbol 'LIVER'. Did you mean: LIVAR?"
    assert fake_catalog.params_for('/genes/variants') == []
    assert fake_catalog.params_for('/genes/genomic-elements') == []


async def test_find_associations_gene_symbol_shaped_like_ca_id(fake_catalog):
    fake_catalog.add('/genes', [{'_id': 'ENSG00000104267', 'name': 'CA2'}])
    fake_catalog.add('/genes/diseases', [{'disease': 'ontology_terms/x'}])

    data = response_json(
        await call_tool('igvf_catalog_find_associations', {'entity_id': 'CA2', 'relationship': 'genetic'})
    )

    assert data['entity_type'] == 'gene'
    assert data['num_associations'] == 1
    assert fake_catalog.params_for('/genes') == [{'name': 'CA2', 'limit': '500', 'page': '0'}]
    assert fake_catalog.params_for('/genes/diseases') == [{'gene_id': 'ENSG00000104267', 'page': '0', 'limit': '25'}]


async def test_find_associations_drug_name_resolved_to_id(fake_catalog):
    fake_catalog.add(
        '/drugs', [{'_id': 'PA166131395', 'name': '10-hydroxy r-warfarin'}, {'_id': 'PA451906', 'name': 'warfarin'}]
    )
    fake_catalog.add('/drugs/variants', [{'variant': 'variants/x'}])

    data = response_json(
        await call_tool(
            'igvf_catalog_find_associations',
            {'entity_id': 'Warfarin', 'hint': 'drug', 'relationship': 'pharmacological'},
        )
    )

    assert data['resolved_entities'] == [{'id': 'PA451906', 'name': 'warfarin'}]
    assert fake_catalog.params_for('/drugs') == [{'name': 'Warfarin', 'limit': '100', 'page': '0'}]
    assert fake_catalog.params_for('/drugs/variants') == [{'drug_id': 'PA451906', 'page': '0', 'limit': '25'}]


async def test_find_associations_protein_name_queries_each_protein(fake_catalog):
    fake_catalog.add(
        '/proteins',
        [{'_id': 'ENSP00000264010', 'name': 'CTCF'}, {'_id': 'ENSP00000494538', 'name': 'CTCF'},
         {'_id': 'ENSP00000391234', 'name': 'CTCFL'}],
    )
    fake_catalog.add('/proteins/transcripts', [{'transcript': 'transcripts/x'}])
    fake_catalog.add('/gene-products/go-terms', [{'go_term_name': 'DNA binding'}])

    data = response_json(
        await call_tool(
            'igvf_catalog_find_associations', {'entity_id': 'ctcf', 'hint': 'protein', 'relationship': 'all'}
        )
    )

    assert [entity['id'] for entity in data['resolved_entities']] == ['ENSP00000264010', 'ENSP00000494538']
    assert fake_catalog.params_for('/proteins') == [
        {'name': 'ctcf', 'limit': '50', 'page': '0'},
        {'uniprot_name': 'ctcf', 'limit': '50', 'page': '0'},
        {'uniprot_full_name': 'ctcf', 'limit': '50', 'page': '0'},
    ]
    assert fake_catalog.params_for('/proteins/transcripts') == [
        {'protein_id': 'ENSP00000264010', 'page': '0', 'limit': '25'},
        {'protein_id': 'ENSP00000494538', 'page': '0', 'limit': '25'},
    ]
    assert fake_catalog.params_for('/gene-products/go-terms') == [
        {'query': 'ENSP00000264010', 'page': '0', 'limit': '25'},
        {'query': 'ENSP00000494538', 'page': '0', 'limit': '25'},
    ]
    metadata = {m['endpoint']: m for m in data['query_metadata']}
    assert metadata['proteins_transcripts']['results_count'] == 2
    assert metadata['go_terms_annotations']['params_used']['query'] == ['ENSP00000264010', 'ENSP00000494538']
    for request_path, params in fake_catalog.requests:
        if request_path != '/proteins':
            assert not {'name', 'protein_name', 'gene_name'} & set(params)


async def test_find_associations_complex_name_without_exact_match(fake_catalog):
    fake_catalog.add('/complexes', [{'_id': 'CPX-5989', 'name': 'Nuclear mitotic cohesin complex, STAG1 variant'}])

    result = await call_tool(
        'igvf_catalog_find_associations', {'entity_id': 'cohesin', 'hint': 'complex', 'relationship': 'physical'}
    )

    assert result[0].text == (
        "No complex found with name 'cohesin'. "
        'Did you mean: Nuclear mitotic cohesin complex, STAG1 variant (CPX-5989)?'
    )
    assert fake_catalog.params_for('/complexes') == [{'name': 'cohesin', 'page': '0'}]
    assert fake_catalog.params_for('/complexes/proteins') == []


async def test_find_associations_protein_go_terms(fake_catalog):
    fake_catalog.add('/gene-products/go-terms', [{'go_term_name': 'DNA repair'}])

    data = response_json(
        await call_tool('igvf_catalog_find_associations', {'entity_id': 'P49711', 'relationship': 'functional'})
    )

    assert data['associations'][0]['_endpoint'] == 'go_terms_annotations'
    assert fake_catalog.params_for('/gene-products/go-terms') == [{'query': 'P49711', 'page': '0', 'limit': '25'}]


async def test_find_associations_uniprot_accession_uses_dbxrefs(fake_catalog):
    fake_catalog.add('/proteins/proteins', [{'protein 2': 'proteins/x'}])

    fake_catalog.add(
        '/proteins',
        [
            {'_id': 'ENSP00000264010', 'uniprot_names': ['CTCF_HUMAN']},
            {'_id': 'ENSP00000494538', 'uniprot_names': ['CTCF_HUMAN']},
        ],
    )
    fake_catalog.add('/proteins/complexes', [{'complex': 'complexes/x'}])

    data = response_json(
        await call_tool('igvf_catalog_find_associations', {'entity_id': 'P49711', 'relationship': 'physical'})
    )

    assert data['num_associations'] == 2
    assert fake_catalog.params_for('/proteins/proteins') == [{'dbxrefs': 'P49711', 'page': '0', 'limit': '25'}]
    assert fake_catalog.params_for('/proteins') == [{'dbxrefs': 'P49711', 'limit': '50', 'page': '0'}]
    assert fake_catalog.params_for('/proteins/complexes') == [
        {'uniprot_name': 'CTCF_HUMAN', 'page': '0', 'limit': '25'}
    ]
    metadata = {m['endpoint']: m for m in data['query_metadata']}
    assert metadata['proteins_complexes']['resolved_from'] == 'dbxrefs'
    assert metadata['proteins_complexes']['params_used']['uniprot_name'] == ['CTCF_HUMAN']
    assert 'resolved_from' not in metadata['proteins_proteins']


async def test_find_associations_rsid_resolved_to_spdi_for_coding(fake_catalog):
    fake_catalog.add(
        '/variants',
        [{'spdi': 'NC_000022.11:43928846:C:G'}, {'spdi': 'NC_000022.11:43928846:C:T'}],
    )
    fake_catalog.add('/variants/coding-variants', [{'coding_variant': 'coding_variants/x'}])

    data = response_json(
        await call_tool('igvf_catalog_find_associations', {'entity_id': 'rs738409', 'relationship': 'coding'})
    )

    assert fake_catalog.params_for('/variants') == [{'rsid': 'rs738409', 'limit': '500', 'page': '0'}]
    assert fake_catalog.params_for('/variants/coding-variants') == [
        {'spdi': 'NC_000022.11:43928846:C:G', 'page': '0', 'limit': '25'},
        {'spdi': 'NC_000022.11:43928846:C:T', 'page': '0', 'limit': '25'},
    ]
    assert data['num_associations'] == 2
    assert [a['_endpoint'] for a in data['associations']] == ['variants_coding_variants'] * 2
    metadata = data['query_metadata'][0]
    assert metadata['resolved_from'] == 'rsid'
    assert metadata['results_count'] == 2
    assert metadata['_pagination']['has_more'] is False
    assert metadata['params_used']['spdi'] == ['NC_000022.11:43928846:C:G', 'NC_000022.11:43928846:C:T']
    assert 'error' not in metadata


async def test_find_associations_reports_capped_limit(fake_catalog):
    fake_catalog.add('/genes', [BRCA1])

    data = response_json(
        await call_tool(
            'igvf_catalog_find_associations',
            {'entity_id': 'BRCA1', 'relationship': 'all', 'limit': 200},
        )
    )

    metadata = {m['endpoint']: m for m in data['query_metadata']}
    assert metadata['genes_genes']['limit_capped_to'] == 100
    assert data['_pagination']['limit'] == 200
    assert data['_pagination']['limit_capped_to'] == {
        'genes_diseases': 25, 'genes_genes': 100, 'genes_transcripts': 100
    }
    assert metadata['genes_genes']['params_used']['limit'] == 100
    assert 'limit_capped_to' not in metadata['genes_variants']
    assert fake_catalog.params_for('/genes/genes') == [{'gene_id': 'ENSG00000012048', 'page': '0', 'limit': '100'}]


async def test_find_associations_uppercase_rsid_is_normalized(fake_catalog):
    fake_catalog.add('/variants', [{'spdi': 'NC_000022.11:43928846:C:G'}])
    fake_catalog.add('/variants/coding-variants', [{'coding_variant': 'coding_variants/x'}])

    data = response_json(
        await call_tool('igvf_catalog_find_associations', {'entity_id': 'RS738409', 'relationship': 'coding'})
    )

    assert data['entity_id'] == 'rs738409'
    assert data['num_associations'] == 1
    assert fake_catalog.params_for('/variants')[0]['rsid'] == 'rs738409'


async def test_find_associations_unresolved_rsid_is_reported(fake_catalog):
    data = response_json(
        await call_tool('igvf_catalog_find_associations', {'entity_id': 'rs1', 'relationship': 'coding'})
    )

    metadata = data['query_metadata'][0]
    assert metadata['results_count'] == 0
    assert metadata['note'] == "No variant found with rsid='rs1', so this endpoint was not queried."
    assert fake_catalog.params_for('/variants/coding-variants') == []


async def test_find_associations_gene_symbol_shaped_like_uniprot_accession(fake_catalog):
    fake_catalog.add('/genes', [{'_id': 'ENSG00000169313', 'name': 'P2RY12'}])
    fake_catalog.add('/genes/variants', [{'variant': 'variants/x'}])

    data = response_json(
        await call_tool('igvf_catalog_find_associations', {'entity_id': 'P2RY12', 'relationship': 'regulatory'})
    )

    assert data['entity_type'] == 'gene'
    assert fake_catalog.params_for('/genes') == [{'name': 'P2RY12', 'limit': '500', 'page': '0'}]
    assert fake_catalog.params_for('/genes/variants') == [{'gene_id': 'ENSG00000169313', 'page': '0', 'limit': '25'}]


async def test_find_associations_hint_selects_protein(fake_catalog):
    await call_tool(
        'igvf_catalog_find_associations', {'entity_id': 'P2RY12', 'relationship': 'physical', 'hint': 'protein'}
    )

    assert fake_catalog.params_for('/genes') == []
    assert fake_catalog.params_for('/proteins/proteins') == [{'dbxrefs': 'P2RY12', 'page': '0', 'limit': '25'}]


async def test_find_associations_hint_disease_name(fake_catalog):
    fake_catalog.add(
        '/ontology-terms',
        [
            {'term_id': 'MONDO_0004670', 'name': 'lupus erythematosus', 'synonyms': ['lupus', 'lupus erythematosus']},
            {'term_id': 'MONDO_0007915', 'name': 'systemic lupus erythematosus', 'synonyms': ['SLE']},
            {'term_id': 'NCIT_C27153', 'name': 'lupus erythematosus', 'synonyms': ['Lupus']},
        ],
    )
    fake_catalog.add('/phenotypes/variants', [{'variant': 'variants/x'}])

    data = response_json(
        await call_tool(
            'igvf_catalog_find_associations', {'entity_id': 'lupus', 'relationship': 'genetic', 'hint': 'disease'}
        )
    )

    assert data['entity_type'] == 'ontology'
    assert data['resolved_entities'] == [
        {'id': 'MONDO_0004670', 'name': 'lupus erythematosus'},
        {'id': 'NCIT_C27153', 'name': 'lupus erythematosus'},
    ]
    assert fake_catalog.params_for('/ontology-terms') == [
        {'name': 'lupus', 'limit': '1000', 'page': '0'},
        {'synonyms': 'lupus', 'limit': '1000', 'page': '0'},
    ]
    assert fake_catalog.params_for('/phenotypes/variants') == [
        {'phenotype_id': 'MONDO_0004670', 'page': '0', 'limit': '25'},
        {'phenotype_id': 'NCIT_C27153', 'page': '0', 'limit': '25'},
    ]
    assert fake_catalog.params_for('/diseases/genes') == [
        {'disease_id': 'MONDO_0004670', 'page': '0', 'limit': '25'},
        {'disease_id': 'NCIT_C27153', 'page': '0', 'limit': '25'},
    ]
    metadata = {m['endpoint']: m for m in data['query_metadata']}
    assert metadata['phenotypes_variants']['resolved_from'] == 'name'
    assert metadata['diseases_genes']['params_used']['disease_id'] == ['MONDO_0004670', 'NCIT_C27153']


async def test_find_associations_disease_name_matching_only_a_synonym(fake_catalog):
    fake_catalog.add(
        '/ontology-terms', [{'term_id': 'HP_0012345', 'name': 'sleep disorder', 'synonyms': []}], params={'name': 'SLE'}
    )
    fake_catalog.add(
        '/ontology-terms',
        [
            {'term_id': 'MONDO_0007915', 'name': 'systemic lupus erythematosus', 'synonyms': ['SLE']},
            {'term_id': 'EFO_0002690', 'name': 'obsolete_systemic lupus erythematosus', 'synonyms': ['SLE', 'lupus']},
            {'term_id': 'MONDO_0000001', 'name': 'other', 'synonyms': ['SLE-like']},
        ],
        params={'synonyms': 'SLE'},
    )
    fake_catalog.add('/phenotypes/variants', [{'variant': 'variants/x'}], params={'phenotype_id': 'EFO_0002690'})

    data = response_json(
        await call_tool(
            'igvf_catalog_find_associations', {'entity_id': 'SLE', 'relationship': 'genetic', 'hint': 'disease'}
        )
    )

    assert [entity['id'] for entity in data['resolved_entities']] == ['MONDO_0007915', 'EFO_0002690']
    assert data['num_associations'] == 1
    assert [params['phenotype_id'] for params in fake_catalog.params_for('/phenotypes/variants')] == [
        'MONDO_0007915',
        'EFO_0002690',
    ]


async def test_find_associations_disease_name_merges_name_and_synonym_matches(fake_catalog):
    mondo = {'term_id': 'MONDO_0004670', 'name': 'lupus erythematosus', 'synonyms': ['lupus']}
    efo = {'term_id': 'EFO_0002690', 'name': 'obsolete_systemic lupus erythematosus', 'synonyms': ['SLE', 'lupus']}
    fake_catalog.add('/ontology-terms', [mondo], params={'name': 'lupus'})
    fake_catalog.add('/ontology-terms', [efo, mondo], params={'synonyms': 'lupus'})

    data = response_json(
        await call_tool(
            'igvf_catalog_find_associations', {'entity_id': 'lupus', 'relationship': 'genetic', 'hint': 'disease'}
        )
    )

    assert [entity['id'] for entity in data['resolved_entities']] == ['MONDO_0004670', 'EFO_0002690']


async def test_find_associations_protein_uniprot_name(fake_catalog):
    proteins = [
        {'_id': 'ENSP00000264010', 'name': 'CTCF', 'uniprot_names': ['CTCF_HUMAN']},
        {'_id': 'ENSP00000494538', 'name': 'CTCF', 'uniprot_names': ['CTCF_HUMAN']},
    ]
    fake_catalog.add('/proteins', proteins, params={'uniprot_name': 'CTCF_HUMAN'})
    fake_catalog.add('/proteins/transcripts', [{'transcript': 'transcripts/x'}])

    data = response_json(
        await call_tool(
            'igvf_catalog_find_associations',
            {'entity_id': 'CTCF_HUMAN', 'hint': 'protein', 'relationship': 'transcription'},
        )
    )

    assert [entity['id'] for entity in data['resolved_entities']] == ['ENSP00000264010', 'ENSP00000494538']
    assert data['num_associations'] == 2
    assert {params['uniprot_name'] for params in fake_catalog.params_for('/proteins') if 'uniprot_name' in params} == {
        'CTCF_HUMAN'
    }


async def test_find_associations_name_suggestions_come_from_every_search(fake_catalog):
    fake_catalog.add('/ontology-terms', [{'term_id': 'HP_1', 'name': 'sleep disorder'}], params={'name': 'SLEx'})
    fake_catalog.add('/ontology-terms', [{'term_id': 'NCIT_1', 'name': 'SLE-like'}], params={'synonyms': 'SLEx'})

    result = await call_tool(
        'igvf_catalog_find_associations', {'entity_id': 'SLEx', 'relationship': 'genetic', 'hint': 'disease'}
    )

    assert result[0].text == (
        "No ontology term found with name 'SLEx'. Did you mean: sleep disorder (HP_1), SLE-like (NCIT_1)?"
    )


async def test_find_associations_ontology_term(fake_catalog):
    fake_catalog.add('/phenotypes/variants', [{'variant': 'variants/x'}])

    await call_tool('igvf_catalog_find_associations', {'entity_id': 'EFO_0004611', 'relationship': 'genetic'})

    assert fake_catalog.params_for('/phenotypes/variants') == [
        {'phenotype_id': 'EFO_0004611', 'page': '0', 'limit': '25'}
    ]
    assert fake_catalog.params_for('/diseases/genes') == [{'disease_id': 'EFO_0004611', 'page': '0', 'limit': '25'}]


async def test_find_associations_limit_is_per_endpoint_and_paginates(fake_catalog):
    fake_catalog.add('/genes/genes', [{'i': i} for i in range(3)])
    fake_catalog.add('/genes/pathways', [{'i': i} for i in range(3)])

    data = response_json(
        await call_tool(
            'igvf_catalog_find_associations',
            {'entity_id': 'ENSG00000163874', 'relationship': 'all', 'limit': 3, 'page': 2},
        )
    )

    assert data['num_associations'] == 6
    assert len(data['associations']) == 6
    assert data['_pagination']['has_more'] is True
    assert data['_pagination']['next_page'] == 3
    assert data['_pagination']['results_returned'] == 6
    assert fake_catalog.params_for('/genes/genes') == [{'gene_id': 'ENSG00000163874', 'page': '2', 'limit': '3'}]


async def test_find_associations_returns_rows_from_every_endpoint(fake_catalog):
    fake_catalog.add('/genes', [BRCA1])
    fake_catalog.add('/genes/variants', [{'variant': f'variants/{i}'} for i in range(2)])
    fake_catalog.add('/genes/genomic-elements', [{'genomic_element': f'genomic_elements/{i}'} for i in range(2)])

    data = response_json(
        await call_tool(
            'igvf_catalog_find_associations', {'entity_id': 'BRCA1', 'relationship': 'regulatory', 'limit': 2}
        )
    )

    endpoints = [a['_endpoint'] for a in data['associations']]
    assert endpoints == ['genes_variants'] * 2 + ['genes_genomic_elements'] * 2
    assert data['num_associations'] == len(data['associations']) == 4
    assert data['_pagination']['results_returned'] == 4
    assert data['_pagination']['has_more'] is True
    assert [m['results_count'] for m in data['query_metadata']] == [2, 2]
    assert all(m['_pagination']['has_more'] for m in data['query_metadata'])


async def test_find_associations_endpoint_error_is_reported(fake_catalog):
    fake_catalog.add('/genes/genes', {'message': 'boom'}, status=500)

    with pytest.raises(ToolError) as error:
        await call_tool('igvf_catalog_find_associations', {'entity_id': 'ENSG00000163874', 'relationship': 'physical'})

    assert str(error.value).startswith('Error finding associations: genes_genes: (500)')
    assert 'boom' in str(error.value)


async def test_find_associations_partial_endpoint_error_is_reported(fake_catalog):
    fake_catalog.add('/genes', [BRCA1])
    fake_catalog.add('/genes/variants', {'message': 'boom'}, status=500)
    fake_catalog.add('/genes/genomic-elements', [{'genomic_element': 'genomic_elements/x'}])

    data = response_json(
        await call_tool('igvf_catalog_find_associations', {'entity_id': 'BRCA1', 'relationship': 'regulatory'})
    )

    assert data['num_associations'] == 1
    assert 'boom' in data['query_metadata'][0]['error']


async def test_find_associations_unknown_relationship(fake_catalog):
    with pytest.raises(ToolError, match='^Unknown relationship type: nope'):
        await call_tool('igvf_catalog_find_associations', {'entity_id': 'rs1', 'relationship': 'nope'})

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


async def test_find_ld_empty_later_page(fake_catalog):
    data = response_json(await call_tool('igvf_catalog_find_ld', {'variant_id': 'rs58542926', 'page': 1}))

    assert data['ld_variants'] == []
    assert data['num_ld_variants'] == 0
    assert data['_pagination'] == {'current_page': 1, 'limit': 100, 'results_returned': 0, 'has_more': False}
    assert 'message' not in data


async def test_find_associations_no_capped_limit(fake_catalog):
    data = response_json(
        await call_tool('igvf_catalog_find_associations', {'entity_id': 'ENSG00000012048', 'relationship': 'genetic'})
    )

    assert 'limit_capped_to' not in data['_pagination']


async def test_find_ld_rejects_non_variant(fake_catalog):
    with pytest.raises(ToolError, match='^Error: Expected a variant ID, but got gene'):
        await call_tool('igvf_catalog_find_ld', {'variant_id': 'ENSG00000163874'})

    assert fake_catalog.requests == []


# resolve_id


async def test_resolve_id_variant(fake_catalog, sample_variant_data):
    fake_catalog.add('/variants', [sample_variant_data])

    data = response_json(await call_tool('igvf_catalog_resolve_id', {'id': 'CA6028682'}))

    assert data['entity_type'] == 'variant'
    assert data['identifiers']['rsid'] == ['rs80357906']
    assert data['identifiers']['spdi'] == 'NC_000017.11:43044295:G:A'
    assert data['identifiers']['position'] == 43044295
    assert data['alleles'] == [
        {'spdi': 'NC_000017.11:43044295:G:A', 'hgvs': 'NC_000017.11:g.43044296G>A', 'ca_id': 'CA6028682',
         'ref': 'G', 'alt': 'A', 'gnomad_af_total': 0.00001}
    ]
    assert 'note' not in data
    assert fake_catalog.params_for('/variants') == [{'ca_id': 'CA6028682', 'limit': '500', 'page': '0'}]


def rs58542926_alleles(af_a, af_t):
    return [
        {'_id': f'NC_000019.10:19268739:C:{alt}', 'rsid': ['rs58542926'], 'spdi': f'NC_000019.10:19268739:C:{alt}',
         'hgvs': f'NC_000019.10:g.19268740C>{alt}', 'ca_id': ca_id, 'ref': 'C', 'alt': alt,
         'annotations': {'bravo_af': 0.01, 'gnomad_af_total': af}}
        for alt, ca_id, af in [('A', 'CA404925740', af_a), ('T', 'CA9324761', af_t)]
    ]


async def test_resolve_id_multi_allelic_rsid(fake_catalog):
    fake_catalog.add('/variants', rs58542926_alleles(None, 0.058314))

    data = response_json(await call_tool('igvf_catalog_resolve_id', {'id': 'rs58542926'}))

    assert data['identifiers']['spdi'] == 'NC_000019.10:19268739:C:T'
    assert data['identifiers']['ca_id'] == 'CA9324761'
    assert [a['spdi'] for a in data['alleles']] == ['NC_000019.10:19268739:C:A', 'NC_000019.10:19268739:C:T']
    assert [a['ca_id'] for a in data['alleles']] == ['CA404925740', 'CA9324761']
    assert [a['gnomad_af_total'] for a in data['alleles']] == [None, 0.058314]
    assert 'multi-allelic' in data['note']
    assert 'highest gnomAD allele frequency (NC_000019.10:19268739:C:T)' in data['note']
    assert fake_catalog.params_for('/genes') == [{'name': 'RS58542926', 'limit': '500', 'page': '0'}]
    assert fake_catalog.params_for('/variants') == [{'rsid': 'rs58542926', 'limit': '500', 'page': '0'}]


async def test_resolve_id_multi_allelic_rsid_without_frequencies(fake_catalog):
    fake_catalog.add('/variants', rs58542926_alleles(None, None))

    data = response_json(await call_tool('igvf_catalog_resolve_id', {'id': 'rs58542926'}))

    assert data['identifiers']['spdi'] == 'NC_000019.10:19268739:C:A'
    assert 'the first one, as no allele has gnomAD allele frequency data' in data['note']


async def test_resolve_id_gene(fake_catalog, sample_gene_data):
    fake_catalog.add('/genes', [sample_gene_data])

    data = response_json(await call_tool('igvf_catalog_resolve_id', {'id': 'HGNC:1101'}))

    assert data['identifiers']['gene_id'] == 'ENSG00000139618'
    assert data['identifiers']['synonyms'] == ['FANCD1', 'BRCC2']
    assert fake_catalog.params_for('/genes') == [{'hgnc_id': 'HGNC:1101', 'page': '0'}]


async def test_resolve_id_ontology_term(fake_catalog):
    fake_catalog.add(
        '/ontology-terms',
        [{'term_id': 'MONDO_0009861', 'name': 'phenylketonuria', 'synonyms': ['PKU'], 'source': 'MONDO'}],
    )

    data = response_json(await call_tool('igvf_catalog_resolve_id', {'id': 'mondo_0009861'}))

    assert data['identifiers'] == {
        'term_id': 'MONDO_0009861', 'name': 'phenylketonuria', 'synonyms': ['PKU'], 'source': 'MONDO'
    }
    assert fake_catalog.params_for('/ontology-terms') == [{'term_id': 'MONDO_0009861', 'page': '0'}]


async def test_resolve_id_uniprot_accession(fake_catalog):
    fake_catalog.add('/proteins', [{'_id': 'ENSP00000494538', 'dbxrefs': [{'name': 'UniProtKB', 'id': 'P49711'}]}])

    data = response_json(await call_tool('igvf_catalog_resolve_id', {'id': 'P49711'}))

    assert data['identifiers']['protein_id'] == 'ENSP00000494538'
    assert data['identifiers']['uniprot_accession'] == 'P49711'
    assert 'note' not in data
    assert fake_catalog.params_for('/proteins') == [{'dbxrefs': 'P49711', 'limit': '50', 'page': '0'}]


async def test_resolve_id_protein_isoforms_prefer_mane_select(fake_catalog):
    dbxrefs = [{'name': 'PDB', 'id': f'{i}ABC'} for i in range(1000)]
    proteins = [
        {'_id': f'ENSP0000048440{i}', 'name': 'TP53', 'uniprot_ids': [f'P04637-{i}'], 'uniprot_names': ['P53_HUMAN'],
         'uniprot_full_names': ['Cellular tumor antigen p53'], 'MANE_Select': i == 1, 'dbxrefs': dbxrefs}
        for i in [9, 1, 2]
    ]
    fake_catalog.add('/proteins', proteins)

    data = response_json(await call_tool('igvf_catalog_resolve_id', {'id': 'P04637'}))

    assert data['identifiers'] == {
        'protein_id': 'ENSP00000484401',
        'name': 'TP53',
        'uniprot_ids': ['P04637-1'],
        'uniprot_names': ['P53_HUMAN'],
        'uniprot_full_names': ['Cellular tumor antigen p53'],
        'uniprot_accession': 'P04637',
        'MANE_Select': True,
        'dbxrefs_count': 1000,
    }
    assert data['proteins'] == [
        {'protein_id': f'ENSP0000048440{i}', 'name': 'TP53', 'uniprot_ids': [f'P04637-{i}'],
         'uniprot_names': ['P53_HUMAN'], 'MANE_Select': i == 1}
        for i in [9, 1, 2]
    ]
    assert 'matches 3 proteins' in data['note']
    assert 'MANE Select protein (ENSP00000484401)' in data['note']


async def test_resolve_id_protein_without_mane_select(fake_catalog):
    fake_catalog.add('/proteins', [{'_id': 'ENSP1', 'MANE_Select': False}, {'_id': 'ENSP2', 'MANE_Select': False}])

    data = response_json(await call_tool('igvf_catalog_resolve_id', {'id': 'P49711'}))

    assert data['identifiers']['protein_id'] == 'ENSP1'
    assert 'the first one, as none is MANE Select' in data['note']


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
    with pytest.raises(ToolError, match='^Unknown category: nope'):
        await call_tool('igvf_catalog_list_sources', {'category': 'nope'})


async def test_unknown_tool():
    with pytest.raises(ValueError, match='Unknown tool'):
        await call_tool('igvf_catalog_nope', {})


# MCP protocol errors


async def call_tool_request(name, arguments):
    request = types.CallToolRequest(
        method='tools/call', params=types.CallToolRequestParams(name=name, arguments=arguments)
    )
    return (await app.request_handlers[types.CallToolRequest](request)).root


@pytest.mark.parametrize(
    ('name', 'arguments', 'message'),
    [
        ('igvf_catalog_search_region', {'region': 'chr1:200-100'}, 'must be less than end'),
        ('igvf_catalog_search_region', {'region': 'chr1-100'}, 'Invalid region format'),
        (
            'igvf_catalog_find_associations',
            {'entity_id': 'MONDO_0007915', 'relationship': 'physical'},
            'not applicable to ontology entities',
        ),
        ('igvf_catalog_get_entity', {'id': '???'}, 'Could not detect entity type'),
        ('igvf_catalog_resolve_id', {'id': '???'}, 'Could not detect entity type'),
        ('igvf_catalog_find_ld', {'variant_id': 'BRCA1'}, 'Expected a variant ID'),
        ('igvf_catalog_list_sources', {'endpoint': 'nope'}, 'Unknown endpoint: nope'),
        ('igvf_catalog_get_entity', {'id': 'BRCA1', 'hint': 'variant'}, 'is not a variant identifier'),
        ('igvf_catalog_get_entity', {'id': 'ENST00000264010', 'hint': 'protein'}, 'is a transcript ID, not a protein'),
        (
            'igvf_catalog_find_associations',
            {'entity_id': 'MONDO_0007915', 'relationship': 'genetic', 'hint': 'gene'},
            'is an ontology term ID, not a gene name',
        ),
    ],
)
async def test_invalid_input_is_a_tool_error(fake_catalog, name, arguments, message):
    result = await call_tool_request(name, arguments)

    assert result.isError is True
    assert message in result.content[0].text


async def test_api_error_is_a_tool_error(fake_catalog):
    fake_catalog.add('/variants', {'message': 'Internal error'}, status=500)

    result = await call_tool_request('igvf_catalog_resolve_id', {'id': 'rs58542926'})

    assert result.isError is True
    assert 'Internal error' in result.content[0].text


async def test_not_found_is_not_a_tool_error(fake_catalog):
    result = await call_tool_request('igvf_catalog_get_entity', {'id': 'ENSG00000000001'})

    assert result.isError is False
    assert result.content[0].text == "No gene found with gene_id='ENSG00000000001'"
