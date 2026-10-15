"""Tests for ID parser."""

import pytest

from igvf_catalog_mcp.services.id_parser import IDParser, name_matches, name_not_found


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


@pytest.mark.parametrize(
    ('identifier', 'hint', 'message'),
    [
        ('ENST00000264010', 'protein', "'ENST00000264010' is a transcript ID, not a protein name."),
        ('MONDO_0007915', 'gene', "'MONDO_0007915' is an ontology term ID, not a gene name."),
        ('ENSG00000139618', 'disease', "'ENSG00000139618' is a gene ID, not a disease name."),
        ('NC_000019.10:19268739:C:T', 'drug', "'NC_000019.10:19268739:C:T' is a variant ID, not a drug name."),
        ('ENSG00000139618', 'variant', "'ENSG00000139618' is a gene ID, not a variant ID."),
        ('CPX-9', 'gene', "'CPX-9' is a complex ID, not a gene name."),
        ('R-HSA-164843', 'gene', "'R-HSA-164843' is a pathway ID, not a gene name."),
        ('P49711-2', 'gene', "'P49711-2' is a protein ID, not a gene name."),
    ],
)
def test_hint_rejects_ids_of_other_types(identifier, hint, message):
    with pytest.raises(ValueError) as error:
        IDParser.detect_entity_type(identifier, hint=hint)
    assert str(error.value) == message


@pytest.mark.parametrize(
    ('identifier', 'hint', 'expected'),
    [
        ('P2RY12', 'gene', ('gene', 'name')),
        ('RS1', 'gene', ('gene', 'name')),
        ('CA1', 'gene', ('gene', 'name')),
        ('CA1', 'protein', ('protein', 'name')),
        ('PA2G4', 'protein', ('protein', 'name')),
    ],
)
def test_hint_accepts_symbol_shaped_ids_as_names(identifier, hint, expected):
    assert IDParser.detect_entity_type(identifier, hint=hint) == expected


@pytest.mark.parametrize(
    'symbol',
    ['HLA-A', 'HLA-DRB1', 'NKX2-1', 'MT-ND1', 'LINC00473', 'ZNF33A-AS1', 'C1orf112', 'hsa-mir-423',
     'ARHGAP27P1-BPTFP1-KPNA2P3'],
)
def test_detect_gene_symbols_with_hyphens_and_lowercase(symbol):
    assert IDParser.detect_entity_type(symbol) == ('gene', 'name')


@pytest.mark.parametrize(
    ('identifier', 'expected'),
    [
        ('CPX-9', ('complex', 'complex_id')),
        ('R-HSA-164843', ('pathway', 'id')),
        ('P49711-2', ('protein', 'protein_id')),
        ('ENSG00000139618', ('gene', 'gene_id')),
    ],
)
def test_hyphenated_ids_keep_their_type(identifier, expected):
    assert IDParser.detect_entity_type(identifier) == expected


@pytest.mark.parametrize('identifier', ['HLA-', '-HLA', 'HLA--A', 'A', 'A' * 26])
def test_reject_malformed_gene_symbols(identifier):
    with pytest.raises(ValueError, match='Could not detect entity type'):
        IDParser.detect_entity_type(identifier)


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
    gene = {'_id': 'ENSG00000169313', 'name': 'P2RY12'}
    fake_catalog.add('/genes', [gene])

    identification = await IDParser.identify('p2ry12')

    assert identification[:3] == ('gene', 'name', 'P2RY12')
    assert identification.matches == [gene]
    assert fake_catalog.params_for('/genes') == [{'name': 'P2RY12', 'limit': '500', 'page': '0'}]


async def test_identify_uniprot_accession_without_matching_gene(fake_catalog):
    fake_catalog.add('/genes', [{'_id': 'ENSG00000000001', 'name': 'P4971'}])

    identification = await IDParser.identify('P49711')

    assert identification == ('protein', 'dbxrefs', 'P49711', None, None)


@pytest.mark.parametrize(
    ('identifier', 'symbol'),
    [('RS1', 'RS1'), ('rs1', 'RS1'), ('CA1', 'CA1'), ('ca2', 'CA2'), ('PA2', 'PA2'), ('GCST1', 'GCST1')],
)
async def test_identify_gene_symbol_shaped_like_other_ids(fake_catalog, identifier, symbol):
    gene = {'_id': 'ENSG00000102104', 'name': symbol}
    fake_catalog.add('/genes', [gene])

    identification = await IDParser.identify(identifier)

    assert identification == ('gene', 'name', symbol, [gene], [])
    assert fake_catalog.params_for('/genes') == [{'name': symbol, 'limit': '500', 'page': '0'}]


@pytest.mark.parametrize(
    ('identifier', 'expected'),
    [
        ('rs7903146', ('variant', 'rsid', 'rs7903146')),
        ('CA9324761', ('variant', 'ca_id', 'CA9324761')),
        ('RS1', ('variant', 'rsid', 'rs1')),
    ],
)
async def test_identify_symbol_shaped_ids_without_exact_gene(fake_catalog, identifier, expected):
    fake_catalog.add('/genes', [{'_id': 'ENSG00000102104', 'name': 'RS1L'}])

    assert await IDParser.identify(identifier) == (*expected, None, None)
    assert len(fake_catalog.params_for('/genes')) == 1


async def test_identify_gene_symbol_keeps_only_exact_matches(fake_catalog):
    brca1 = {'_id': 'ENSG00000012048', 'name': 'BRCA1'}
    brca2 = {'_id': 'ENSG00000139618', 'name': 'BRCA2'}
    fake_catalog.add('/genes', [brca2, brca1])

    assert await IDParser.identify('brca1') == ('gene', 'name', 'BRCA1', [brca1], [brca2])
    assert await IDParser.identify('BRCA', hint='gene') == ('gene', 'name', 'BRCA', [], [brca2, brca1])


async def test_identify_long_ids_skip_gene_check(fake_catalog):
    assert await IDParser.identify('ENSG00000139618') == ('gene', 'gene_id', 'ENSG00000139618', None, None)
    assert await IDParser.identify('rs123456789') == ('variant', 'rsid', 'rs123456789', None, None)
    assert fake_catalog.requests == []


@pytest.mark.parametrize(
    ('identifier', 'expected'),
    [
        ('CPX-9', ('complex', 'complex_id', 'CPX-9')),
        ('r-hsa-164843', ('pathway', 'id', 'R-HSA-164843')),
        ('P49711-2', ('protein', 'protein_id', 'P49711-2')),
        ('ENSP00000264010', ('protein', 'protein_id', 'ENSP00000264010')),
    ],
)
async def test_identify_hyphenated_and_long_ids_skip_gene_check(fake_catalog, identifier, expected):
    assert await IDParser.identify(identifier) == (*expected, None, None)
    assert fake_catalog.requests == []


async def test_identify_hyphenated_gene_symbol(fake_catalog):
    genes = [{'_id': 'ENSG00000206503', 'name': 'HLA-A'}, {'_id': 'ENSG00000206505', 'name': 'HLA-A'}]
    fake_catalog.add('/genes', [*genes, {'_id': 'ENSG00000204525', 'name': 'HLA-C'}])

    identification = await IDParser.identify('hla-a')

    assert identification[:4] == ('gene', 'name', 'HLA-A', genes)
    assert fake_catalog.params_for('/genes') == [{'name': 'HLA-A', 'limit': '500', 'page': '0'}]


async def test_identify_gene_symbol_keeps_catalog_case(fake_catalog):
    gene = {'_id': 'ENSG00000000460', 'name': 'C1orf112'}
    fake_catalog.add('/genes', [gene])

    assert await IDParser.identify('C1ORF112') == ('gene', 'name', 'C1orf112', [gene], [])
    assert fake_catalog.params_for('/genes') == [{'name': 'C1ORF112', 'limit': '500', 'page': '0'}]


async def test_identify_hint_skips_gene_check(fake_catalog):
    assert await IDParser.identify('P2RY12', hint='protein') == ('protein', 'dbxrefs', 'P2RY12', None, None)
    assert await IDParser.identify('rs1', hint='variant') == ('variant', 'rsid', 'rs1', None, None)
    assert await IDParser.identify('CA1', hint='variant') == ('variant', 'ca_id', 'CA1', None, None)
    assert fake_catalog.requests == []


async def test_lookup_name_matches_other_names_case_insensitively(fake_catalog):
    lupus = {'term_id': 'MONDO_0004670', 'name': 'lupus erythematosus', 'synonyms': ['lupus']}
    sle = {'term_id': 'MONDO_0007915', 'name': 'systemic lupus erythematosus', 'synonyms': ['SLE']}
    fake_catalog.add('/ontology-terms', [lupus, sle])

    assert await IDParser.lookup_name('ontology', 'Lupus') == ([lupus], [sle])


@pytest.mark.parametrize(
    ('entity_type', 'path', 'params'),
    [
        ('ontology', '/ontology-terms', ['name', 'synonyms']),
        ('protein', '/proteins', ['name', 'uniprot_name', 'uniprot_full_name']),
        ('gene', '/genes', ['name']),
        ('drug', '/drugs', ['name']),
        ('complex', '/complexes', ['name']),
    ],
)
async def test_lookup_name_searches_every_name_field(fake_catalog, entity_type, path, params):
    await IDParser.lookup_name(entity_type, 'x')

    assert [next(iter(set(request) - {'limit', 'page'})) for request in fake_catalog.params_for(path)] == params


async def test_lookup_name_merges_candidates_by_id(fake_catalog):
    lupus = {'term_id': 'MONDO_0004670', 'name': 'lupus erythematosus', 'synonyms': ['lupus']}
    efo = {'term_id': 'EFO_0002690', 'name': 'obsolete_systemic lupus erythematosus', 'synonyms': ['lupus']}
    sle = {'term_id': 'MONDO_0007915', 'name': 'systemic lupus erythematosus', 'synonyms': ['SLE']}
    fake_catalog.add('/ontology-terms', [lupus, sle], params={'name': 'lupus'})
    fake_catalog.add('/ontology-terms', [efo, lupus], params={'synonyms': 'lupus'})

    assert await IDParser.lookup_name('ontology', 'lupus') == ([lupus, efo], [sle])


@pytest.mark.parametrize(
    ('entity', 'name'),
    [
        ({'name': 'CTCF', 'uniprot_names': ['CTCF_HUMAN']}, 'ctcf'),
        ({'name': 'CTCF', 'uniprot_names': ['CTCF_HUMAN']}, 'ctcf_human'),
        ({'name': 'CTCF', 'uniprot_full_names': ['Transcriptional repressor CTCF']}, 'transcriptional repressor ctcf'),
    ],
)
def test_name_matches_protein_fields(entity, name):
    assert name_matches(entity, 'protein', name)


def test_name_matches_is_exact():
    assert not name_matches({'name': 'LIVAR'}, 'gene', 'LIVER')
    assert not name_matches({'name': 'warfarin'}, 'drug', 'warfarin sodium')
    assert name_matches({'name': 'warfarin'}, 'drug', 'Warfarin')


def test_name_not_found_suggests_near_matches():
    assert name_not_found('gene', 'LIVER', [{'_id': 'ENSG00000266304', 'name': 'LIVAR'}]) == (
        "No gene found with symbol 'LIVER'. Did you mean: LIVAR?"
    )
    assert name_not_found('drug', 'warfarine', []) == "No drug found with name 'warfarine'"
    assert name_not_found('ontology', 'lupu', [{'term_id': 'MONDO_0004670', 'name': 'lupus erythematosus'}]) == (
        "No ontology term found with name 'lupu'. Did you mean: lupus erythematosus (MONDO_0004670)?"
    )
    many = [{'name': f'GENE{i}'} for i in range(12)]
    assert name_not_found('gene', 'GENE', many).endswith('GENE9, …?')
