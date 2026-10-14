"""Entity ID parser with auto-detection of entity types."""

import re
from typing import Literal

from .api_client import get_client

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

# Entity type for each accepted hint
HINT_TYPES: dict[str, str] = {
    **{entity_type: entity_type for entity_type in ENTITY_METHODS},
    'disease': 'ontology',
}

# Lookup parameter used when a hinted identifier is a name rather than an ID
NAME_PARAMS: dict[str, str] = {
    'gene': 'name',
    'protein': 'name',
    'ontology': 'name',
    'drug': 'name',
    'complex': 'name',
    'pathway': 'name',
}

# Maximum page size of each lookup method. The complexes and studies methods take no limit and return
# API_PAGE_SIZE results per page.
ENTITY_MAX_LIMITS: dict[str, int] = {
    'gene': 500,
    'transcript': 500,
    'protein': 50,
    'variant': 500,
    'ontology': 1000,
    'drug': 100,
    'pathway': 500,
}

# Default page size of the IGVF Catalog API
API_PAGE_SIZE = 25

# Gene symbol format; some symbols (e.g. P2RY12, B3GAT1) are also valid UniProt accessions
GENE_SYMBOL = r'^[A-Z][A-Z0-9]{1,9}$'

# Generic ontology term ID: a prefix of letters, _ or :, and a local ID containing a digit (e.g. NCIT_C27153)
ONTOLOGY_TERM = r'^([A-Z]+)[_:]([A-Z0-9]*\d[A-Z0-9]*)$'

# Change part of a genomic HGVS ID: a substitution, or a deletion, duplication, insertion or deletion-insertion
GENOMIC_HGVS_CHANGE = r'(?:\d+[A-Z]>[A-Z]|\d+(?:_\d+)?(?:del|dup)|\d+_\d+ins[A-Z]+|\d+(?:_\d+)?delins[A-Z]+)'

# UniProt accession format (https://www.uniprot.org/help/accession_numbers)
UNIPROT_ACCESSION = r'(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})'


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
        # UniProt isoforms like P49711-2 are protein IDs; bare accessions are cross-references
        (rf'^{UNIPROT_ACCESSION}-\d+$', 'protein', 'protein_id'),
        (rf'^{UNIPROT_ACCESSION}$', 'protein', 'dbxrefs'),
        # Variants
        (r'^rs\d+$', 'variant', 'rsid'),
        (r'^NC_\d+\.\d+:\d+:[A-Z]*:[A-Z]*$', 'variant', 'spdi'),
        (rf'^NC_\d+\.\d+:g\.{GENOMIC_HGVS_CHANGE}$', 'variant', 'hgvs'),
        (r'^CA\d+$', 'variant', 'ca_id'),
        # Ontology terms
        (r'^Orphanet[_:]\d+$', 'ontology', 'term_id'),
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
        # Other ontology terms (e.g. HP_0033726, NCIT_C27153); after the specific patterns, which use : and - too
        (ONTOLOGY_TERM, 'ontology', 'term_id'),
        # Gene symbols (must be last, as it's most ambiguous)
        (GENE_SYMBOL, 'gene', 'name'),
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
            ValueError: If the identifier format is not recognized, or the hint is unknown or does not
                fit the identifier
        """
        # Normalize identifier
        identifier = identifier.strip()

        # A hint selects the entity type; identifiers that are not IDs of that type are looked up by name
        if hint:
            hinted_type = HINT_TYPES.get(hint.lower())
            if hinted_type is None:
                raise ValueError(f"Unknown hint: '{hint}'. Valid hints: {', '.join(HINT_TYPES)}")
            for pattern, entity_type, param_name in cls.PATTERNS:
                if entity_type == hinted_type and re.match(pattern, identifier, re.IGNORECASE):
                    return entity_type, param_name  # type: ignore
            if hinted_type in NAME_PARAMS:
                return hinted_type, NAME_PARAMS[hinted_type]  # type: ignore
            raise ValueError(
                f"'{identifier}' is not a {hint} identifier, and {hint} entities cannot be looked up by name."
            )

        # Try pattern matching
        for pattern, entity_type, param_name in cls.PATTERNS:
            if re.match(pattern, identifier, re.IGNORECASE):
                return entity_type, param_name  # type: ignore

        raise ValueError(
            f'Could not detect entity type for identifier: {identifier}. '
            f'Supported formats include: ENSG* (genes), rs* (variants), ENSP* (proteins), '
            f'NC_* (variants), ontology terms such as MONDO_0007915 or HP_0033726, and gene symbols.'
        )

    @classmethod
    async def identify(cls, identifier: str, hint: str | None = None) -> tuple[EntityType, str, str]:
        """
        Detect the entity type of an identifier and normalize it for API queries.

        Without a hint, an identifier that is both a UniProt accession and a gene symbol is a gene
        if a gene with exactly that symbol exists, and a protein otherwise.

        Args:
            identifier: The ID string to parse
            hint: Optional hint about the entity type

        Returns:
            Tuple of (entity_type, parameter_name, normalized_identifier)

        Raises:
            ValueError: As detect_entity_type
        """
        entity_type, param_name = cls.detect_entity_type(identifier, hint)
        normalized_id = cls.normalize_identifier(identifier, entity_type, param_name)

        if hint is None and param_name == 'dbxrefs' and re.match(GENE_SYMBOL, normalized_id):
            genes = await get_client().call(ENTITY_METHODS['gene'], name=normalized_id, page=0)
            if any(gene.get('name') == normalized_id for gene in genes):
                return 'gene', 'name', normalized_id

        return entity_type, param_name, normalized_id

    @classmethod
    async def lookup_all(cls, entity_type: EntityType, param_name: str, identifier: str) -> list[dict]:
        """
        Look up every entity matching an identifier, across all pages.

        Args:
            entity_type: The type of entity
            param_name: The lookup parameter
            identifier: The normalized identifier

        Returns:
            All matching entities (e.g. every allele of an rsID)
        """
        return await get_client().call_all(
            cls.get_client_method(entity_type),
            ENTITY_MAX_LIMITS.get(entity_type, API_PAGE_SIZE),
            **{param_name: identifier},
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
    def normalize_identifier(cls, identifier: str, entity_type: EntityType, param_name: str) -> str:
        """
        Normalize an identifier for API queries.

        IDs are matched case-insensitively, so they are converted to the case the catalog stores.
        Names are passed through, except gene symbols, which are uppercase.

        Args:
            identifier: The raw identifier
            entity_type: The detected entity type
            param_name: The lookup parameter returned by detect_entity_type

        Returns:
            Normalized identifier
        """
        identifier = identifier.strip()
        original = identifier

        if param_name == 'name':
            if entity_type == 'gene':
                identifier = identifier.upper()
            return identifier

        if param_name == 'rsid':
            return identifier.lower()

        identifier = identifier.upper()
        if param_name == 'hgvs':
            sequence, change = identifier.split(':G.', 1)
            change = re.sub(r'DELINS|DEL|DUP|INS', lambda match: match.group().lower(), change)
            identifier = f'{sequence}:g.{change}'
        if entity_type == 'ontology':
            return cls.normalize_term_id(original)

        return identifier

    @classmethod
    def normalize_term_id(cls, term_id: str) -> str:
        """
        Normalize an ontology term ID to the form the catalog stores.

        Separators are stored as underscores and IDs are uppercase, except mixed-case prefixes such as
        Orphanet_ or VariO_. A mixed-case prefix is kept as typed; Orphanet is recognised in any case.

        Args:
            term_id: The stripped term ID

        Returns:
            Normalized term ID
        """
        match = re.match(ONTOLOGY_TERM, term_id, re.IGNORECASE)
        if match is None:
            return term_id.upper().replace(':', '_')
        prefix, local_id = match.groups()
        if prefix.upper() == 'ORPHANET':
            prefix = 'Orphanet'
        elif prefix.islower() or prefix.isupper():
            prefix = prefix.upper()
        return f'{prefix}_{local_id.upper()}'
