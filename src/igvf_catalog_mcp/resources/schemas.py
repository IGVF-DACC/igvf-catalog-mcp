"""MCP resources for entity schemas."""

from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.types import Resource

# Gene schema
GENE_SCHEMA = Resource(
    uri='igvf://schemas/gene',
    name='Gene Entity Schema',
    mimeType='application/json',
    description='Schema and field descriptions for gene entities',
)

GENE_SCHEMA_CONTENT = """
{
  "entity_type": "gene",
  "description": "Protein-coding and non-coding genes from GENCODE, as returned by igvf_catalog_get_entity",
  "fields": {
    "_type": "Entity type added by this server ('gene')",
    "_id": "Ensembl gene ID (ENSG* for human, ENSMUSG* for mouse)",
    "chr": "Chromosome (e.g., 'chr1', 'chrX')",
    "start": "Start position (0-based; GRCh38 for human, GRCm39 for mouse)",
    "end": "End position (exclusive; 0-based, half-open)",
    "name": "Gene symbol (e.g., 'BRCA1', 'TP53')",
    "gene_type": "Type of gene (protein_coding, lncRNA, miRNA, etc.)",
    "strand": "Strand (+/-)",
    "hgnc": "HGNC ID (e.g., 'HGNC:1100')",
    "entrez": "Entrez Gene ID (e.g., 'ENTREZ:672')",
    "synonyms": "List of gene name aliases",
    "collections": "Gene collections (ACMG73, GREGoR, etc.)",
    "study_sets": "Associated study sets",
    "source": "Data source (GENCODE)",
    "version": "GENCODE version (e.g., 'v43')",
    "source_url": "URL of the GENCODE file the gene was loaded from"
  },
  "notes": "Mouse genes have only _id, chr, start, end, gene_type, name, entrez, source, version and source_url."
}
"""

# Variant schema
VARIANT_SCHEMA = Resource(
    uri='igvf://schemas/variant',
    name='Variant Entity Schema',
    mimeType='application/json',
    description='Schema and field descriptions for genetic variants',
)

VARIANT_SCHEMA_CONTENT = """
{
  "entity_type": "variant",
  "description": "Genetic variants (human variants from FAVOR), as returned by igvf_catalog_get_entity",
  "fields": {
    "_type": "Entity type added by this server ('variant')",
    "_id": "Variant ID; for human variants the SPDI (NC_*:pos:ref:alt)",
    "organism": "Homo sapiens or Mus musculus",
    "chr": "Chromosome (e.g., 'chr7')",
    "pos": "Position (0-based, GRCh38; same as the SPDI position)",
    "rsid": "List of dbSNP rsIDs (e.g., ['rs3757387'])",
    "ref": "Reference allele",
    "alt": "Alternate allele",
    "spdi": "SPDI format (e.g., 'NC_000007.14:128936031:T:C')",
    "hgvs": "HGVS format (e.g., 'NC_000007.14:g.128936032T>C'; 1-based)",
    "ca_id": "ClinGen Allele Registry ID (e.g., 'CA12520929'); may be null",
    "qual": "Quality from the source VCF",
    "files_filesets": "IGVF file the variant was loaded from, if any",
    "source": "Data source (e.g., 'FAVOR')",
    "source_url": "URL of the data source",
    "annotations": {
      "bravo_af": "Allele frequency in BRAVO",
      "gnomad_af_*": "gnomAD allele frequencies: total, raw, by sex, by population, by both (gnomad_af_nfe_female)",
      "GENCODE_category": "coding or noncoding"
    }
  },
  "coordinate_system": "0-based, half-open intervals"
}
"""

# Identifier guide
IDENTIFIER_GUIDE = Resource(
    uri='igvf://guide/identifiers',
    name='Identifier Format Guide',
    mimeType='text/markdown',
    description='How to recognize and format different ID types',
)

IDENTIFIER_GUIDE_CONTENT = """
# Identifier Format Guide

## Genes
- **Ensembl**: ENSG00000139618 (starts with ENSG); mouse ENSMUSG00000000001 (starts with ENSMUSG)
- **Gene Symbol**: BRCA1, TP53 (2-10 uppercase letters/numbers)
- **HGNC**: HGNC:1100 (HGNC:digits)
- **Entrez**: ENTREZ:672 (the ENTREZ: prefix is required; a bare number is not recognized)

## Variants
All four of these name the same variant:
- **rsID**: rs3757387 (starts with 'rs'; one rsID can cover several alleles)
- **SPDI**: NC_000007.14:128936031:T:C (RefSeq:pos:ref:alt, 0-based position)
- **HGVS**: NC_000007.14:g.128936032T>C (RefSeq:g.pos ref>alt, 1-based position)
- **ClinGen**: CA12520929 (starts with 'CA')

## Proteins
- **Ensembl**: ENSP00000493376 (starts with ENSP); mouse ENSMUSP00000000001 (starts with ENSMUSP)
- **UniProt**: P49711, P49711-2 (6 alphanumeric + optional -isoform); human or mouse (e.g. Q9DC51)

## Transcripts
- **Ensembl**: ENST00000443707 (starts with ENST); mouse ENSMUST00000000001 (starts with ENSMUST)

## Organisms
Genes, transcripts, proteins and variants are looked up in Homo sapiens unless `organism` is "Mus musculus".
Mouse Ensembl IDs are always looked up in Mus musculus, and UniProt accessions and protein names that match no human
protein are also looked up in Mus musculus.

## Ontology Terms
- **Disease**: Orphanet_586, MONDO_0008199, DOID_0050741
- **Cell Type**: CL_0000084
- **Tissue**: UBERON_0002048
- **Phenotype**: EFO_0004340, OBA_0000128
- **Gene Ontology**: GO_0008150

## Other
- **Drug**: PA448497 (PharmGKB)
- **Complex**: CPX-9 (Complex Portal)
- **Pathway**: R-HSA-164843 (Reactome)
- **Study**: GCST007798 (GWAS Catalog)

## Coordinate System
The IGVF Catalog uses **0-based, half-open** coordinates:
- Start is inclusive (0-based)
- End is exclusive
- Example: chr1:100-200 includes positions 100-199
- A 1-based position P (as in dbSNP, HGVS or genome browsers) is the region chrN:(P-1)-P, e.g. HGVS
  g.128936032 above is chr7:128936031-128936032
"""

# Example queries
EXAMPLE_QUERIES = Resource(
    uri='igvf://examples/queries',
    name='Example Queries',
    mimeType='text/markdown',
    description='Common query patterns with expected results',
)

EXAMPLE_QUERIES_CONTENT = """
# Example Queries

## 1. Look up a gene by symbol
```json
Tool: igvf_catalog_get_entity
Input: {"id": "BRCA1"}
Returns: Gene information including coordinates, HGNC ID, Ensembl ID
```

## 2. Find genes, variants and regulatory elements in a region
```json
Tool: igvf_catalog_search_region
Input: {"region": "chr17:41000000-42000000"}
Returns: Genes, variants, and regulatory elements in the region
```

## 3. Find what regulates a gene
```json
Tool: igvf_catalog_find_associations
Input: {"entity_id": "TP53", "relationship": "regulatory"}
Returns: Variants that affect TP53 expression or splicing (eQTLs, sQTLs) and regulatory elements linked to TP53
```

## 4. Convert variant ID formats
```json
Tool: igvf_catalog_resolve_id
Input: {"id": "rs80357906"}
Returns: SPDI, HGVS, ClinGen ID, and genomic coordinates
```

## 5. Find GWAS associations for a variant
```json
Tool: igvf_catalog_find_associations
Input: {"entity_id": "rs3757387", "relationship": "genetic"}
Returns: Phenotypes/diseases associated with the variant (OpenTargets GWAS, e.g. rheumatoid arthritis)
```

## 6. Discover available data sources
```json
Tool: igvf_catalog_list_sources
Input: {"category": "gene_expression"}
Returns: AFGR, EBI eQTL Catalogue, IGVF details
```

## 7. Find protein-protein interactions
```json
Tool: igvf_catalog_find_associations
Input: {"entity_id": "P04637", "relationship": "physical"}
Returns: Interacting proteins (BioGRID, IntAct) and complexes containing TP53
```

## 8. Flexible region formats
All these work:
- chr1:1000000-2000000
- 1:1000000-2000000
- chr1:1,000,000-2,000,000
- chrX:1M-2M
- chr1:1.5M-2.5M

## 9. Look up a protein by UniProt entry name
```json
Tool: igvf_catalog_get_entity
Input: {"id": "HBA_HUMAN", "hint": "protein"}
Returns: The proteins with that UniProt entry name (HBA1 and HBA2). Without the hint, a name is looked up as a
gene symbol.
```

## 10. Query a mouse entity
```json
Tool: igvf_catalog_find_associations
Input: {"entity_id": "Q9DC51", "relationship": "physical"}
Returns: BioGRID interactions of mouse Gnai3. A UniProt accession that matches no human protein is looked up in
Mus musculus; pass "organism": "Mus musculus" to look up gene symbols and names in mouse.
```
"""


# All resources
ALL_RESOURCES = [
    GENE_SCHEMA,
    VARIANT_SCHEMA,
    IDENTIFIER_GUIDE,
    EXAMPLE_QUERIES,
]

_RESOURCE_CONTENT = {
    str(GENE_SCHEMA.uri): GENE_SCHEMA_CONTENT,
    str(VARIANT_SCHEMA.uri): VARIANT_SCHEMA_CONTENT,
    str(IDENTIFIER_GUIDE.uri): IDENTIFIER_GUIDE_CONTENT,
    str(EXAMPLE_QUERIES.uri): EXAMPLE_QUERIES_CONTENT,
}
_RESOURCES_BY_URI = {str(resource.uri): resource for resource in ALL_RESOURCES}


async def get_resource_content(uri: object) -> ReadResourceContents:
    """Get the content and MIME type for a resource URI.

    The MCP SDK passes the URI as a pydantic ``AnyUrl``, so it is compared as a string.
    """
    key = str(uri)
    resource = _RESOURCES_BY_URI.get(key)
    if resource is None:
        raise ValueError(f'Unknown resource URI: {key}')

    return ReadResourceContents(content=_RESOURCE_CONTENT[key].strip(), mime_type=resource.mimeType)
