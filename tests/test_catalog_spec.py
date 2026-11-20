"""Tests for reading the catalog OpenAPI spec shipped in the generated client."""

import importlib

import pytest
from igvf_catalog_async_client import AsyncIgvfCatalogApi

from igvf_catalog_mcp.services import catalog_spec
from igvf_catalog_mcp.services.catalog_spec import (
    SpecError,
    load_spec,
    max_page_size,
    normalize_method_name,
    operation,
    operations,
    param_enum,
    param_schema,
)


def public_client_methods() -> list[str]:
    return [
        name
        for name in dir(AsyncIgvfCatalogApi)
        if not name.startswith('_') and not name.endswith(('_with_http_info', '_without_preload_content'))
        and callable(getattr(AsyncIgvfCatalogApi, name))
    ]


def test_spec_is_shipped_in_the_client():
    spec = load_spec()
    assert spec['openapi'].startswith('3.')
    assert spec['servers'][0]['url'].endswith('/api')


def test_every_client_method_has_exactly_one_operation():
    methods = public_client_methods()
    assert len(methods) == len(operations())
    assert {normalize_method_name(m) for m in methods} == set(operations())


@pytest.mark.parametrize(
    ('client_method', 'path'),
    [
        ('genes_from_variants', '/variants/genes'),
        # operationId variantsFromVariantID: plain camelCase splitting would give variants_from_variant_i_d
        ('variants_from_variant_id', '/variants/variant-ld'),
        ('go_terms_from_annotations', '/gene-products/go-terms'),
    ],
)
def test_operation_path(client_method, path):
    assert operation(client_method)[0] == path


def test_unknown_method():
    with pytest.raises(SpecError, match="no operation for client method 'nope'"):
        operation('nope')


def test_param_enum():
    assert set(param_enum('genes_genes', 'organism')) == {'Homo sapiens', 'Mus musculus'}
    assert 'synthetic lethality (sensu BioGRID)' in param_enum('genes_genes', 'method')
    # A parameter without an enum, and one the operation doesn't have
    assert param_schema('genes_genes', 'gene_id') is not None
    assert param_enum('genes_genes', 'gene_id') is None
    assert param_schema('genes_genes', 'nope') is None
    assert param_enum('genes_genes', 'nope') is None


def test_max_page_size():
    assert max_page_size('genes_genes') == 100
    assert max_page_size('drugs') == 1000
    # Its description states no page size
    assert max_page_size('complexes_from_proteins') is None


def test_missing_spec_names_the_minimum_client(tmp_path, monkeypatch):
    package = tmp_path / 'old_client'
    package.mkdir()
    (package / '__init__.py').write_text('')
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    monkeypatch.setattr(catalog_spec, 'CLIENT_PACKAGE', 'old_client')
    load_spec.cache_clear()
    try:
        with pytest.raises(SpecError, match=r'too old\. Install igvf-catalog-async-client 1\.3\.0\.post1 or later'):
            load_spec()
    finally:
        load_spec.cache_clear()
