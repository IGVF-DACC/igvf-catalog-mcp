"""Tests for ID parser."""

import pytest

from igvf_catalog_mcp.services.id_parser import IDParser


def test_detect_gene_ensembl():
    """Test detection of Ensembl gene IDs."""
    entity_type, param_name = IDParser.detect_entity_type(
        'ENSG00000139618')
    assert entity_type == 'gene'
    assert param_name == 'gene_id'


def test_detect_gene_symbol():
    """Test detection of gene symbols."""
    entity_type, param_name = IDParser.detect_entity_type('BRCA1')
    assert entity_type == 'gene'
    assert param_name == 'name'


def test_detect_gene_hgnc():
    """Test detection of HGNC IDs."""
    entity_type, param_name = IDParser.detect_entity_type('HGNC:1100')
    assert entity_type == 'gene'
    assert param_name == 'hgnc_id'


def test_detect_variant_rsid():
    """Test detection of rsID variants."""
    entity_type, param_name = IDParser.detect_entity_type('rs12345')
    assert entity_type == 'variant'
    assert param_name == 'rsid'


def test_detect_variant_spdi():
    """Test detection of SPDI format variants."""
    entity_type, param_name = IDParser.detect_entity_type(
        'NC_000001.11:12345:A:G')
    assert entity_type == 'variant'
    assert param_name == 'spdi'


def test_detect_variant_hgvs():
    """Test detection of HGVS format variants."""
    entity_type, param_name = IDParser.detect_entity_type(
        'NC_000001.11:g.12346A>G')
    assert entity_type == 'variant'
    assert param_name == 'hgvs'


@pytest.mark.parametrize(
    ('identifier', 'param_name', 'expected'),
    [
        ('NC_000016.10:19999964:A:', 'spdi', 'NC_000016.10:19999964:A:'),
        ('nc_000001.11:1000099::t', 'spdi', 'NC_000001.11:1000099::T'),
        ('NC_000019.10:g.19259535_19259538del', 'hgvs', 'NC_000019.10:g.19259535_19259538del'),
        ('NC_000019.10:G.19259535_19259538DEL', 'hgvs', 'NC_000019.10:g.19259535_19259538del'),
        ('NC_000016.10:g.19999965del', 'hgvs', 'NC_000016.10:g.19999965del'),
        ('nc_000019.10:g.19259538_19259539insagac', 'hgvs', 'NC_000019.10:g.19259538_19259539insAGAC'),
        ('NC_000001.11:g.1000_1001delinsTT', 'hgvs', 'NC_000001.11:g.1000_1001delinsTT'),
        ('NC_000001.11:g.1000_1003DUP', 'hgvs', 'NC_000001.11:g.1000_1003dup'),
        ('NC_000001.11:g.1000dup', 'hgvs', 'NC_000001.11:g.1000dup'),
    ],
)
def test_detect_indel_variants(identifier, param_name, expected):
    assert IDParser.detect_entity_type(identifier) == ('variant', param_name)
    assert IDParser.normalize_identifier(identifier, 'variant', param_name) == expected


@pytest.mark.parametrize('identifier', ['NC_000001.11:g.1000ins', 'NC_000001.11:g.1000insA', 'NC_000001.11:g.1000_del'])
def test_reject_malformed_hgvs(identifier):
    with pytest.raises(ValueError, match='Could not detect entity type'):
        IDParser.detect_entity_type(identifier)


def test_detect_variant_ca_id():
    """Test detection of ClinGen Allele IDs."""
    entity_type, param_name = IDParser.detect_entity_type('CA12345')
    assert entity_type == 'variant'
    assert param_name == 'ca_id'


def test_detect_protein_ensembl():
    """Test detection of Ensembl protein IDs."""
    entity_type, param_name = IDParser.detect_entity_type(
        'ENSP00000493376')
    assert entity_type == 'protein'
    assert param_name == 'protein_id'


def test_detect_protein_uniprot():
    """Bare UniProt accessions are looked up as cross-references, isoforms as protein IDs."""
    assert IDParser.detect_entity_type('P49711') == ('protein', 'dbxrefs')
    assert IDParser.detect_entity_type('P49711-1') == ('protein', 'protein_id')


@pytest.mark.parametrize('symbol', ['TCF7L2', 'PNPLA3', 'VKORC1', 'CYP2C9', 'BRCA1', 'TP53', 'HNF1A'])
def test_gene_symbols_are_not_uniprot_accessions(symbol):
    assert IDParser.detect_entity_type(symbol) == ('gene', 'name')


@pytest.mark.parametrize('accession', ['P49711', 'P49711-1', 'Q9Y6K9', 'A0A024RBG1'])
def test_detect_uniprot_accessions(accession):
    entity_type, _ = IDParser.detect_entity_type(accession)
    assert entity_type == 'protein'


def test_detect_transcript():
    """Test detection of transcript IDs."""
    entity_type, param_name = IDParser.detect_entity_type(
        'ENST00000443707')
    assert entity_type == 'transcript'
    assert param_name == 'transcript_id'


def test_detect_ontology_orphanet():
    """Test detection of Orphanet IDs."""
    entity_type, param_name = IDParser.detect_entity_type('Orphanet_586')
    assert entity_type == 'ontology'
    assert param_name == 'term_id'


def test_detect_ontology_mondo():
    """Test detection of MONDO IDs."""
    entity_type, param_name = IDParser.detect_entity_type('MONDO_0008199')
    assert entity_type == 'ontology'
    assert param_name == 'term_id'


@pytest.mark.parametrize(
    ('identifier', 'expected'),
    [
        ('HP_0033726', 'HP_0033726'),
        ('hp:0033726', 'HP_0033726'),
        ('NCIT_C27153', 'NCIT_C27153'),
        ('ncit:c27153', 'NCIT_C27153'),
        ('PR_000001', 'PR_000001'),
        ('EFO:0002690', 'EFO_0002690'),
        ('VariO_0001', 'VariO_0001'),
        ('Orphanet:586', 'Orphanet_586'),
    ],
)
def test_generic_ontology_term_ids(identifier, expected):
    entity_type, param_name = IDParser.detect_entity_type(identifier)
    assert (entity_type, param_name) == ('ontology', 'term_id')
    assert IDParser.normalize_identifier(identifier, entity_type, param_name) == expected


@pytest.mark.parametrize(
    ('identifier', 'expected'),
    [
        ('HGNC:1100', ('gene', 'hgnc_id')),
        ('ENTREZ:675', ('gene', 'entrez')),
        ('CPX-9', ('complex', 'complex_id')),
        ('R-HSA-164843', ('pathway', 'id')),
        ('Orphanet_586', ('ontology', 'term_id')),
        ('BRCA1', ('gene', 'name')),
    ],
)
def test_generic_ontology_pattern_keeps_specific_patterns(identifier, expected):
    assert IDParser.detect_entity_type(identifier) == expected


def test_disease_hint_treats_ontology_id_as_term_id():
    assert IDParser.detect_entity_type('NCIT_C27153', hint='disease') == ('ontology', 'term_id')


def test_detect_drug():
    """Test detection of drug IDs."""
    entity_type, param_name = IDParser.detect_entity_type('PA448497')
    assert entity_type == 'drug'
    assert param_name == 'drug_id'


def test_detect_complex():
    """Test detection of complex IDs."""
    entity_type, param_name = IDParser.detect_entity_type('CPX-9')
    assert entity_type == 'complex'
    assert param_name == 'complex_id'


def test_detect_pathway():
    """Test detection of pathway IDs."""
    entity_type, param_name = IDParser.detect_entity_type('R-HSA-164843')
    assert entity_type == 'pathway'
    assert param_name == 'id'


def test_detect_with_hint():
    """Test detection with hint parameter."""
    # Gene symbol could be ambiguous, but hint helps
    entity_type, param_name = IDParser.detect_entity_type(
        'TP53', hint='gene')
    assert entity_type == 'gene'
    assert param_name == 'name'


@pytest.mark.parametrize(
    ('identifier', 'hint', 'expected'),
    [
        ('CTCF', 'protein', ('protein', 'name')),
        ('P49711', 'protein', ('protein', 'dbxrefs')),
        ('lupus', 'disease', ('ontology', 'name')),
        ('MONDO_0007915', 'disease', ('ontology', 'term_id')),
        ('warfarin', 'drug', ('drug', 'name')),
        ('rs12345', 'variant', ('variant', 'rsid')),
        ('ENSG00000139618', 'gene', ('gene', 'gene_id')),
    ],
)
def test_hint_selects_entity_type(identifier, hint, expected):
    assert IDParser.detect_entity_type(identifier, hint=hint) == expected


def test_hint_without_name_lookup_rejects_names():
    with pytest.raises(ValueError, match="'BRCA1' is not a variant identifier"):
        IDParser.detect_entity_type('BRCA1', hint='variant')


def test_unknown_hint():
    with pytest.raises(ValueError, match="Unknown hint: 'cell'"):
        IDParser.detect_entity_type('BRCA1', hint='cell')


def test_invalid_identifier():
    """Test that invalid identifiers raise ValueError."""
    with pytest.raises(ValueError, match='Could not detect entity type'):
        IDParser.detect_entity_type('invalid_id_12345!@#')


@pytest.mark.parametrize(
    ('identifier', 'expected'),
    [
        ('brca1', 'BRCA1'),
        ('ensg00000141510', 'ENSG00000141510'),
        ('enst00000443707.2', 'ENST00000443707.2'),
        ('p49711-1', 'P49711-1'),
        ('p49711', 'P49711'),
        ('RS7903146', 'rs7903146'),
        ('nc_000012.12:102917129:t:c', 'NC_000012.12:102917129:T:C'),
        ('nc_000001.11:G.12346a>g', 'NC_000001.11:g.12346A>G'),
        ('ca9324761', 'CA9324761'),
        ('mondo:0008199', 'MONDO_0008199'),
        ('orphanet_586', 'Orphanet_586'),
        ('ORPHANET:586', 'Orphanet_586'),
        ('hgnc:1100', 'HGNC:1100'),
        ('pa448497', 'PA448497'),
        ('cpx-9', 'CPX-9'),
        ('r-hsa-164843', 'R-HSA-164843'),
    ],
)
def test_normalize_identifier_case(identifier, expected):
    entity_type, param_name = IDParser.detect_entity_type(identifier)
    assert IDParser.normalize_identifier(identifier, entity_type, param_name) == expected


def test_normalize_keeps_names():
    assert IDParser.normalize_identifier(' lupus ', 'ontology', 'name') == 'lupus'
    assert IDParser.normalize_identifier('Warfarin', 'drug', 'name') == 'Warfarin'
    assert IDParser.normalize_identifier('ctcf', 'gene', 'name') == 'CTCF'


def test_get_client_method():
    """Test client method retrieval."""
    assert IDParser.get_client_method('gene') == 'genes'
    assert IDParser.get_client_method('variant') == 'variants'
    assert IDParser.get_client_method('protein') == 'proteins'
    assert IDParser.get_client_method('ontology') == 'ontology_term'
    assert IDParser.get_client_method('pathway') == 'pathways'


async def test_identify_gene_symbol_shaped_like_uniprot_accession(fake_catalog):
    fake_catalog.add('/genes', [{'_id': 'ENSG00000169313', 'name': 'P2RY12'}])

    assert await IDParser.identify('p2ry12') == ('gene', 'name', 'P2RY12')
    assert fake_catalog.params_for('/genes') == [{'name': 'P2RY12', 'page': '0'}]


async def test_identify_uniprot_accession_without_matching_gene(fake_catalog):
    fake_catalog.add('/genes', [{'_id': 'ENSG00000000001', 'name': 'P4971'}])

    assert await IDParser.identify('P49711') == ('protein', 'dbxrefs', 'P49711')


async def test_identify_hint_skips_gene_check(fake_catalog):
    assert await IDParser.identify('P2RY12', hint='protein') == ('protein', 'dbxrefs', 'P2RY12')
    assert await IDParser.identify('rs1') == ('variant', 'rsid', 'rs1')
    assert fake_catalog.requests == []
