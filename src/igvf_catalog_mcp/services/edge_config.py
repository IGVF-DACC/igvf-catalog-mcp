"""Edge endpoint configuration for the IGVF Catalog API.

This module defines the structure and parameters for all edge (relationship) endpoints
in the IGVF Catalog API. It provides a centralized configuration that tools can use
to build correct queries with proper parameter names, source values, and filters.

Each endpoint's definition in EDGE_ENDPOINT_DEFINITIONS holds the MCP's own design: which client method it calls,
the entity types it connects, the identifiers and filters it exposes, and descriptive sources where the API has no
source parameter. Everything the API itself states is read from the OpenAPI spec shipped in the generated client
(see catalog_spec) when EDGE_ENDPOINTS is built: the path, the maximum page size, the organisms, and the allowed
source, label and method values.
"""

from typing import Literal, TypedDict

from .api_client import method_params
from .catalog_spec import SpecError, max_page_size, operation, param_enum

EntityType = Literal[
    'gene',
    'transcript',
    'protein',
    'variant',
    'ontology',
    'drug',
    'complex',
    'study',
    'pathway',
    'genomic_element',
    'coding_variant',
]


class EdgeEndpointConfig(TypedDict, total=False):
    """Configuration for an edge endpoint."""

    client_method: str  # AsyncIgvfCatalogApi method name
    path: str  # API path, for display (from the spec)
    from_type: EntityType
    to_type: EntityType
    from_params: list[str]  # Valid parameter names for the "from" entity
    sources: list[str]  # Valid `source` filter values (from the spec), or a description of the data where there is none
    labels: list[str]  # Valid label/edge type values (from the spec)
    methods: list[str]  # Valid method values (from the spec)
    filters: dict[str, str]  # Filter name -> type (range, string, enum)
    max_limit: int  # Maximum page size (from the spec)
    organisms: list[str]  # Values of the organism parameter, where the endpoint has one (from the spec)


GENE_PARAMS = ['gene_id', 'gene_name', 'hgnc_id', 'synonym']
PROTEIN_PARAMS = ['protein_id', 'protein_name', 'uniprot_name', 'uniprot_full_name', 'dbxrefs']
VARIANT_PARAMS = ['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id']

QTL_FILTERS = {
    'neg_log10_pvalue': 'range',
    'effect_size': 'range',
    'biological_context': 'string',
    'files_fileset': 'string',
}

# Configuration keys read from the enum of a spec query parameter, present where the parameter has one
SPEC_ENUM_KEYS: dict[str, str] = {
    'organisms': 'organism',
    'sources': 'source',
    'labels': 'label',
    'methods': 'method',
}

# Configuration keys that come from the spec, which EDGE_ENDPOINT_DEFINITIONS must not set. Exceptions: sources of
# endpoints without a source parameter, and MAX_LIMIT_OVERRIDES.
DERIVED_KEYS = frozenset({'path', 'max_limit', *SPEC_ENUM_KEYS})

# Maximum page size of endpoints whose spec description doesn't state one. Only allowed for those endpoints.
MAX_LIMIT_OVERRIDES: dict[str, int] = {
    'proteins_complexes': 100,
}

# Hand-written part of every edge endpoint; EDGE_ENDPOINTS adds what the spec states
EDGE_ENDPOINT_DEFINITIONS: dict[str, EdgeEndpointConfig] = {
    # Variant-Gene relationships (eQTLs, sQTLs, CRISPR screens)
    'variants_genes': {
        'client_method': 'genes_from_variants',
        'from_type': 'variant',
        'to_type': 'gene',
        'from_params': VARIANT_PARAMS,
        'filters': QTL_FILTERS,
    },
    'genes_variants': {
        'client_method': 'variants_from_genes',
        'from_type': 'gene',
        'to_type': 'variant',
        'from_params': GENE_PARAMS,
        'filters': QTL_FILTERS,
    },
    # Variant-Protein relationships (pQTL, allele-specific binding)
    'variants_proteins': {
        'client_method': 'proteins_from_variants',
        'from_type': 'variant',
        'to_type': 'protein',
        'from_params': VARIANT_PARAMS + ['region'],
        'filters': {
            'files_fileset': 'string',
        },
    },
    'proteins_variants': {
        'client_method': 'variants_from_proteins',
        'from_type': 'protein',
        'to_type': 'variant',
        'from_params': PROTEIN_PARAMS,
        'filters': {
            'files_fileset': 'string',
        },
    },
    # Variant-Phenotype relationships (GWAS)
    'variants_phenotypes': {
        'client_method': 'phenotypes_from_variants',
        'from_type': 'variant',
        'to_type': 'ontology',
        'from_params': VARIANT_PARAMS + ['region'],
        'sources': ['OpenTargets', 'IGVF'],
        'filters': {
            'neg_log10_pvalue': 'range',
            'phenotype_id': 'string',
            'files_fileset': 'string',
        },
    },
    'phenotypes_variants': {
        'client_method': 'variants_from_phenotypes',
        'from_type': 'ontology',
        'to_type': 'variant',
        'from_params': ['phenotype_id', 'phenotype_name'],
        'filters': {
            'neg_log10_pvalue': 'range',
            'files_fileset': 'string',
        },
    },
    # Variant-Drug relationships (PharmGKB)
    'variants_drugs': {
        'client_method': 'drugs_from_variants',
        'from_type': 'variant',
        'to_type': 'drug',
        'from_params': VARIANT_PARAMS,
        'sources': ['PharmGKB'],
        'filters': {
            'pmid': 'string',
            'phenotype_categories': 'enum',
        },
    },
    'drugs_variants': {
        'client_method': 'variants_from_drugs',
        'from_type': 'drug',
        'to_type': 'variant',
        'from_params': ['drug_id', 'drug_name'],
        'sources': ['PharmGKB'],
        'filters': {
            'pmid': 'string',
            'phenotype_categories': 'enum',
        },
    },
    # Variant-Disease relationships (ClinGen)
    'variants_diseases': {
        'client_method': 'disease_from_variants',
        'from_type': 'variant',
        'to_type': 'ontology',
        'from_params': VARIANT_PARAMS,
        'sources': ['ClinGen'],
        'filters': {
            'assertion': 'enum',
            'pmid': 'string',
        },
    },
    # Gene-Disease relationships (Orphanet, ClinGen, GenCC)
    'genes_diseases': {
        'client_method': 'diseases_from_genes',
        'from_type': 'gene',
        'to_type': 'ontology',
        'from_params': GENE_PARAMS,
        'filters': {},
    },
    'diseases_genes': {
        'client_method': 'genes_from_diseases',
        'from_type': 'ontology',
        'to_type': 'gene',
        'from_params': ['disease_id', 'disease_name'],
        'filters': {},
    },
    # Gene-Gene relationships (coexpression, interactions)
    'genes_genes': {
        'client_method': 'genes_genes',
        'from_type': 'gene',
        'to_type': 'gene',
        'from_params': GENE_PARAMS,
        'filters': {
            'z_score': 'range',
            'interaction_type': 'enum',
        },
    },
    # Protein-Protein interactions
    'proteins_proteins': {
        'client_method': 'proteins_proteins',
        'from_type': 'protein',
        'to_type': 'protein',
        'from_params': PROTEIN_PARAMS,
        'filters': {
            'interaction_type': 'enum',
        },
    },
    # Complex-Protein relationships
    'complexes_proteins': {
        'client_method': 'proteins_from_complexes',
        'from_type': 'complex',
        'to_type': 'protein',
        'from_params': ['complex_id', 'complex_name', 'description'],
        'sources': ['EBI Complex Portal'],
        'filters': {},
    },
    'proteins_complexes': {
        'client_method': 'complexes_from_proteins',
        'from_type': 'protein',
        'to_type': 'complex',
        # dbxrefs only narrows a query here; on its own the API requires protein_id, name, uniprot_name or
        # uniprot_full_name, so a bare UniProt accession is resolved to its UniProt name instead
        'from_params': [p for p in PROTEIN_PARAMS if p != 'dbxrefs'],
        'sources': ['EBI Complex Portal'],
        'filters': {},
    },
    # Gene-Pathway relationships
    'genes_pathways': {
        'client_method': 'pathways_from_genes',
        'from_type': 'gene',
        'to_type': 'pathway',
        'from_params': GENE_PARAMS,
        'sources': ['Reactome'],
        'filters': {},
    },
    # Gene-Transcript relationships
    'genes_transcripts': {
        'client_method': 'transcripts_from_genes',
        'from_type': 'gene',
        'to_type': 'transcript',
        'from_params': GENE_PARAMS,
        'sources': ['GENCODE'],
        'filters': {},
    },
    'transcripts_genes': {
        'client_method': 'genes_from_transcripts',
        'from_type': 'transcript',
        'to_type': 'gene',
        'from_params': ['transcript_id', 'region'],
        'sources': ['GENCODE'],
        'filters': {},
    },
    # Transcript-Protein relationships
    'transcripts_proteins': {
        'client_method': 'proteins_from_transcripts',
        'from_type': 'transcript',
        'to_type': 'protein',
        'from_params': ['transcript_id', 'transcript_type', 'region'],
        'sources': ['GENCODE'],
        'filters': {},
    },
    'proteins_transcripts': {
        'client_method': 'transcripts_from_proteins',
        'from_type': 'protein',
        'to_type': 'transcript',
        'from_params': PROTEIN_PARAMS,
        'sources': ['GENCODE'],
        'filters': {},
    },
    # Motif-Protein relationships
    'motifs_proteins': {
        'client_method': 'proteins_from_motifs',
        'from_type': 'ontology',
        'to_type': 'protein',
        'from_params': ['tf_name'],
        'filters': {
            'files_fileset': 'string',
        },
    },
    'proteins_motifs': {
        'client_method': 'motifs_from_proteins',
        'from_type': 'protein',
        'to_type': 'ontology',
        'from_params': PROTEIN_PARAMS,
        'sources': ['IGVF', 'HOCOMOCOv11'],
        'filters': {
            'files_fileset': 'string',
        },
    },
    # Variant-Variant relationships (Linkage Disequilibrium)
    'variants_variants': {
        'client_method': 'variants_from_variant_id',
        'from_type': 'variant',
        'to_type': 'variant',
        'from_params': VARIANT_PARAMS + ['region'],
        'sources': ['TopLD'],
        'filters': {
            'r2': 'range',
            'd_prime': 'range',
            'ancestry': 'enum',
        },
    },
    # Variant-Coding Variant relationships
    'variants_coding_variants': {
        'client_method': 'coding_variants_from_variants',
        'from_type': 'variant',
        'to_type': 'coding_variant',
        'from_params': ['variant_id', 'spdi', 'hgvs', 'ca_id'],
        'sources': ['dbNSFP'],
        'filters': {},
    },
    'coding_variants_variants': {
        'client_method': 'variants_from_coding_variants',
        'from_type': 'coding_variant',
        'to_type': 'variant',
        'from_params': ['coding_variant_name', 'hgvsp'],
        'sources': ['dbNSFP'],
        'filters': {},
    },
    # Variant-Genomic Element relationships (caQTL)
    'variants_genomic_elements': {
        'client_method': 'genomic_elements_from_variants',
        'from_type': 'variant',
        'to_type': 'genomic_element',
        'from_params': VARIANT_PARAMS,
        'sources': ['AFGR', 'IGVF'],
        'filters': {
            'biological_context': 'string',
            'files_fileset': 'string',
        },
    },
    # Genomic Element-Gene relationships (E2G predictions, CRISPR screens)
    'genomic_elements_genes': {
        'client_method': 'genes_from_genomic_elements',
        'from_type': 'genomic_element',
        'to_type': 'gene',
        'from_params': ['region'],
        'filters': {
            'source_annotation': 'enum',
            'region_type': 'enum',
            'biosample_term': 'string',
            'biological_context': 'string',
            'neg_log10_pvalue': 'range',
            'score': 'range',
            'files_fileset': 'string',
        },
    },
    # Gene-Genomic Element relationships (E2G predictions, CRISPR screens), queried from the gene side
    'genes_genomic_elements': {
        'client_method': 'genomic_elements_from_genes',
        'from_type': 'gene',
        'to_type': 'genomic_element',
        'from_params': GENE_PARAMS,
        'filters': {
            'biosample_term': 'string',
            'biological_context': 'string',
            'neg_log10_pvalue': 'range',
            'score': 'range',
            'files_fileset': 'string',
        },
    },
    # Genomic Element-Biosample relationships (MPRA)
    'genomic_elements_biosamples': {
        'client_method': 'biosamples_from_genomic_elements',
        'from_type': 'genomic_element',
        'to_type': 'ontology',
        'from_params': ['region'],
        'filters': {
            'region_type': 'enum',
            'files_fileset': 'string',
        },
    },
    'biosamples_genomic_elements': {
        'client_method': 'genomic_elements_from_biosamples',
        'from_type': 'ontology',
        'to_type': 'genomic_element',
        'from_params': ['biosample_name'],
        'filters': {
            'files_fileset': 'string',
        },
    },
    # GO term annotations
    'go_terms_annotations': {
        'client_method': 'go_terms_from_annotations',
        'from_type': 'protein',
        'to_type': 'ontology',
        'from_params': ['query'],  # Can be protein or transcript ID
        'sources': ['Gene Ontology'],
        'filters': {
            'name': 'enum',  # 'involved in', 'is located in', 'has the function'
        },
    },
}



def derive_endpoint(endpoint_key: str, definition: EdgeEndpointConfig) -> EdgeEndpointConfig:
    """
    Complete an endpoint definition with what the catalog OpenAPI spec states.

    Args:
        endpoint_key: The edge endpoint key
        definition: Its hand-written definition

    Returns:
        The definition plus path, max_limit, and organisms, sources, labels and methods where the spec has an enum
        of the organism, source, label and method parameter. Spec values are in spec order.

    Raises:
        SpecError: If the spec has no operation for the client method, or neither the spec nor MAX_LIMIT_OVERRIDES
            gives a maximum page size
    """
    client_method = definition['client_method']
    path, _ = operation(client_method)
    max_limit = max_page_size(client_method) or MAX_LIMIT_OVERRIDES.get(endpoint_key)
    if max_limit is None:
        raise SpecError(
            f'{endpoint_key}: the spec states no maximum page size for {client_method}; add one to MAX_LIMIT_OVERRIDES'
        )
    config: EdgeEndpointConfig = {**definition, 'path': path, 'max_limit': max_limit}
    for key, param_name in SPEC_ENUM_KEYS.items():
        values = param_enum(client_method, param_name)
        if values is not None:
            config[key] = values
    return config


# Complete edge endpoint registry
EDGE_ENDPOINTS: dict[str, EdgeEndpointConfig] = {
    endpoint_key: derive_endpoint(endpoint_key, definition)
    for endpoint_key, definition in EDGE_ENDPOINT_DEFINITIONS.items()
}

# Relationship type to endpoint mapping for higher-level abstractions
RELATIONSHIP_TYPE_MAPPING = {
    'regulatory': {
        'gene': ['genes_variants', 'genes_genomic_elements'],
        'variant': ['variants_genes', 'variants_genomic_elements'],
        'genomic_element': ['genomic_elements_genes'],
    },
    'genetic': {
        'gene': ['genes_diseases'],
        'variant': ['variants_phenotypes', 'variants_diseases'],
        'ontology': ['phenotypes_variants', 'diseases_genes'],
    },
    'physical': {
        'protein': ['proteins_proteins', 'proteins_complexes'],
        'complex': ['complexes_proteins'],
        'gene': ['genes_genes'],
    },
    'functional': {
        'gene': ['genes_pathways'],
        'protein': ['go_terms_annotations'],
    },
    'pharmacological': {
        'variant': ['variants_drugs'],
        'drug': ['drugs_variants'],
    },
    'ld': {
        'variant': ['variants_variants'],
    },
    'coding': {
        'variant': ['variants_coding_variants'],
        'coding_variant': ['coding_variants_variants'],
    },
    'transcription': {
        'gene': ['genes_transcripts'],
        'transcript': ['transcripts_genes', 'transcripts_proteins'],
        'protein': ['proteins_transcripts'],
    },
}


def get_edge_config(endpoint_key: str) -> EdgeEndpointConfig | None:
    """Get configuration for a specific edge endpoint."""
    return EDGE_ENDPOINTS.get(endpoint_key)


def supports_verbose(config: EdgeEndpointConfig) -> bool:
    """Whether the endpoint's client method accepts the verbose parameter."""
    return 'verbose' in method_params(config['client_method'])


def get_endpoints_for_entity_and_relationship(
    entity_type: EntityType, relationship_type: str
) -> list[str]:
    """
    Get applicable endpoint keys for an entity type and relationship type.

    Args:
        entity_type: Type of the starting entity
        relationship_type: Type of relationship to find

    Returns:
        List of endpoint keys that match the criteria
    """
    if relationship_type not in RELATIONSHIP_TYPE_MAPPING:
        return []

    entity_mapping = RELATIONSHIP_TYPE_MAPPING[relationship_type]
    return entity_mapping.get(entity_type, [])


def get_all_sources() -> set[str]:
    """Get all unique data sources across all endpoints."""
    sources = set()
    for config in EDGE_ENDPOINTS.values():
        if 'sources' in config:
            sources.update(config['sources'])
    return sources


def get_sources_by_category() -> dict[str, list[str]]:
    """Organize sources by category for the list_sources tool."""
    return {
        'variant_annotations': ['dbNSFP', 'ClinGen'],
        'gene_expression': ['AFGR', 'EBI', 'IGVF'],
        'regulatory': ['ADASTRA', 'GVATdb', 'UKB', 'ENCODE', 'IGVF'],
        'disease': ['Orphanet', 'ClinGen', 'GenCC', 'OpenTargets'],
        'drugs': ['PharmGKB'],
        'interactions': ['BioGRID', 'IntAct', 'COXPRESdb', 'EBI Complex Portal'],
        'studies': ['GWAS Catalog', 'OpenTargets'],
        'structure': ['GENCODE'],
        'linkage': ['TopLD'],
        'motifs': ['HOCOMOCOv11', 'IGVF'],
        'pathways': ['Reactome'],
        'ontology': ['Gene Ontology'],
    }
