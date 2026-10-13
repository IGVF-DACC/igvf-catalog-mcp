"""Entity ID parser with auto-detection of entity types."""

import re
from typing import Literal

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
]

# Generated client method used to look up each entity type
ENTITY_METHODS: dict[str, str] = {
    'gene': 'genes',
    'transcript': 'transcripts',
    'protein': 'proteins',
    'variant': 'variants',
    'ontology': 'ontology_term',
    'drug': 'drugs',
    'complex': 'complexes',
    'study': 'studies',
    'pathway': 'pathways',
}


class IDParser:
    """Parse and detect entity types from various ID formats."""

    # Pattern definitions for entity type detection
    PATTERNS = [
        # Genes
        (r'^ENSG\d+(\.\d+)?$', 'gene', 'gene_id'),
        (r'^HGNC:\d+$', 'gene', 'hgnc_id'),
        (r'^ENTREZ:\d+$', 'gene', 'entrez'),
        # Transcripts
        (r'^ENST\d+(\.\d+)?$', 'transcript', 'transcript_id'),
        # Proteins
        (r'^ENSP\d+(\.\d+)?$', 'protein', 'protein_id'),
        # UniProt format like P49711-2
        (r'^[A-Z0-9]{6}(-\d+)?$', 'protein', 'protein_id'),
        # Variants
        (r'^rs\d+$', 'variant', 'rsid'),
        (r'^NC_\d+\.\d+:\d+:[A-Z]+:[A-Z]+$', 'variant', 'spdi'),
        (r'^NC_\d+\.\d+:g\.\d+[A-Z]>[A-Z]$', 'variant', 'hgvs'),
        (r'^CA\d+$', 'variant', 'ca_id'),
        # Ontology terms
        (r'^Orphanet_\d+$', 'ontology', 'term_id'),
        (r'^MONDO[_:]\d+$', 'ontology', 'term_id'),
        (r'^EFO[_:]\d+$', 'ontology', 'term_id'),
        (r'^GO[_:]\d+$', 'ontology', 'term_id'),
        (r'^DOID[_:]\d+$', 'ontology', 'term_id'),
        (r'^UBERON[_:]\d+$', 'ontology', 'term_id'),
        (r'^CL[_:]\d+$', 'ontology', 'term_id'),
        (r'^CHEBI[_:]\d+$', 'ontology', 'term_id'),
        (r'^OBA[_:]\d+$', 'ontology', 'term_id'),
        # Drugs
        (r'^PA\d+$', 'drug', 'drug_id'),
        # Complexes
        (r'^CPX-\d+$', 'complex', 'complex_id'),
        # Studies
        (r'^GCST\d+$', 'study', 'study_id'),
        # Pathways
        (r'^R-[A-Z]{3}-\d+$', 'pathway', 'id'),
        # Gene symbols (must be last, as it's most ambiguous)
        (r'^[A-Z][A-Z0-9]{1,9}$', 'gene', 'name'),
    ]

    @classmethod
    def detect_entity_type(
        cls, identifier: str, hint: str | None = None
    ) -> tuple[EntityType, str]:
        """
        Detect entity type from an identifier string.

        Args:
            identifier: The ID string to parse
            hint: Optional hint about the entity type

        Returns:
            Tuple of (entity_type, parameter_name), where parameter_name is the keyword
            argument of the entity's lookup method (see get_client_method)

        Raises:
            ValueError: If the identifier format is not recognized
        """
        # Normalize identifier
        identifier = identifier.strip()

        # If hint is provided and matches, use it
        if hint:
            hint_lower = hint.lower()
            for pattern, entity_type, param_name in cls.PATTERNS:
                if entity_type == hint_lower and re.match(pattern, identifier, re.IGNORECASE):
                    return entity_type, param_name  # type: ignore

        # Try pattern matching
        for pattern, entity_type, param_name in cls.PATTERNS:
            if re.match(pattern, identifier, re.IGNORECASE):
                return entity_type, param_name  # type: ignore

        raise ValueError(
            f'Could not detect entity type for identifier: {identifier}. '
            f'Supported formats include: ENSG* (genes), rs* (variants), ENSP* (proteins), '
            f'NC_* (variants), Orphanet_*/MONDO_*/EFO_* (ontology terms), and gene symbols.'
        )

    @classmethod
    def get_client_method(cls, entity_type: EntityType) -> str:
        """
        Get the generated client method used to look up an entity type.

        Args:
            entity_type: The type of entity

        Returns:
            AsyncIgvfCatalogApi method name (e.g., "genes", "variants")
        """
        return ENTITY_METHODS[entity_type]

    @classmethod
    def normalize_identifier(cls, identifier: str, entity_type: EntityType) -> str:
        """
        Normalize an identifier for API queries.

        Args:
            identifier: The raw identifier
            entity_type: The detected entity type

        Returns:
            Normalized identifier
        """
        identifier = identifier.strip()

        # Normalize ontology term separators to underscores
        if entity_type == 'ontology':
            identifier = identifier.replace(':', '_')

        # Convert gene symbols to uppercase
        if entity_type == 'gene' and re.match(r'^[A-Z][A-Z0-9]{1,9}$', identifier, re.IGNORECASE):
            identifier = identifier.upper()

        return identifier
