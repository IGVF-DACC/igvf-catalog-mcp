"""Entity ID parser with auto-detection of entity types."""

import asyncio
import re
from typing import Any, Literal, NamedTuple

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

# Display name of entity types in messages
TYPE_LABELS: dict[str, str] = {'ontology': 'ontology term'}

# Lookup parameter used when a hinted identifier is a name rather than an ID
NAME_PARAMS: dict[str, str] = {
    'gene': 'name',
    'protein': 'name',
    'ontology': 'name',
    'drug': 'name',
    'complex': 'name',
    'pathway': 'name',
}

# Record fields that a name must equal (case-insensitively) for an entity to match it exactly
NAME_FIELDS: dict[str, list[str]] = {
    'gene': ['name'],
    'protein': ['name', 'uniprot_names', 'uniprot_full_names'],
    'ontology': ['name', 'synonyms'],
    'drug': ['name'],
    'complex': ['name'],
    'pathway': ['name'],
}

# Lookup parameters searched for name candidates: one per field of NAME_FIELDS that the API can search. Gene
# symbols are only matched against the symbol, so genes are not searched by synonym.
NAME_LOOKUP_PARAMS: dict[str, list[str]] = {
    'gene': ['name'],
    'protein': ['name', 'uniprot_name', 'uniprot_full_name'],
    'ontology': ['name', 'synonyms'],
    'drug': ['name'],
    'complex': ['name'],
    'pathway': ['name'],
}

# Record field holding each entity type's ID
ID_FIELDS: dict[str, str] = {'ontology': 'term_id'}

# Maximum number of near matches suggested when a name has no exact match
MAX_SUGGESTIONS = 10

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

# Gene symbol format: alphanumeric parts separated by hyphens (e.g. BRCA1, C1orf112, HLA-DRB1, ZNF33A-AS1), up to the
# length of the catalog's longest symbols (readthrough genes such as ARHGAP27P1-BPTFP1-KPNA2P3)
GENE_SYMBOL = r'^(?=.{2,25}$)[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*$'

# Gene symbols that can also fit other ID patterns: some symbols (e.g. P2RY12, B3GAT1) are also valid UniProt
# accessions, others (RS1, CA1) rsIDs or CA IDs. No catalog symbol with a hyphen or more than 10 characters fits one.
ID_SHAPED_SYMBOL = r'^[A-Z][A-Z0-9]{1,9}$'

# Prefixes of the ontology term IDs the catalog stores, in the catalog's case: the loaded ontologies and the terms they
# import (collected from every page of /ontology-terms)
ONTOLOGY_PREFIXES = [
    'AfPO', 'BAO', 'BFO', 'BSPO', 'BTO', 'CARO', 'CHEBI', 'CHMO', 'CL', 'CLM', 'CLO', 'COB', 'CVCL', 'DDANAT', 'DHBA',
    'DISDRIV', 'DOID', 'ECO', 'ECTO', 'EFO', 'ENVO', 'EO', 'ExO', 'FBbi', 'FBbt', 'FBdv', 'FMA', 'FOODON', 'GAZ',
    'GENO', 'GO', 'GOREL', 'GSSO', 'HANCESTRO', 'HBA', 'HP', 'HsapDv', 'IAO', 'IDO', 'MA', 'MAXO', 'MBA', 'MF',
    'MFOMD', 'MIM', 'MOD', 'MONDO', 'MOP', 'MP', 'MPATH', 'MRO', 'NBO', 'NCBITaxon', 'NCIT', 'NTR', 'OBA', 'OBI',
    'OGMS', 'OMIABIS', 'OMIT', 'OMO', 'OMRSE', 'OPL', 'Orphanet', 'PATO', 'PCL', 'PCO', 'PO', 'PR', 'REO', 'RO', 'SIO',
    'SLM', 'SO', 'STATO', 'SYMP', 'TO', 'TRANS', 'UBERON', 'UBPROP', 'UBREL', 'UO', 'UPHENO', 'VO', 'VariO', 'WBls',
    'ZEA', 'ZFA',
]

# Canonical case of each ontology prefix, by lowercase prefix
ONTOLOGY_PREFIX_CASE: dict[str, str] = {prefix.lower(): prefix for prefix in ONTOLOGY_PREFIXES}

# Ontology term ID: a known prefix (in any case), _ or :, and a local ID containing a digit (e.g. NCIT_C27153)
ONTOLOGY_TERM = rf"^({'|'.join(ONTOLOGY_PREFIXES)})[_:]([A-Z0-9]*\d[A-Z0-9]*)$"

# Change part of a genomic HGVS ID: a substitution, or a deletion, duplication, insertion or deletion-insertion
GENOMIC_HGVS_CHANGE = r'(?:\d+[A-Z]>[A-Z]|\d+(?:_\d+)?(?:del|dup)|\d+_\d+ins[A-Z]+|\d+(?:_\d+)?delins[A-Z]+)'

# UniProt accession format (https://www.uniprot.org/help/accession_numbers)
UNIPROT_ACCESSION = r'(?:[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})'


class Identification(NamedTuple):
    """An identifier's entity type, lookup parameter and normalized value."""

    entity_type: EntityType
    param_name: str
    identifier: str
    # Entities whose name equals the identifier, when it was looked up by name (gene symbols); otherwise None
    matches: list[dict[str, Any]] | None = None
    # Other entities the name lookup returned
    near_matches: list[dict[str, Any]] | None = None


def entity_id(entity: dict[str, Any], entity_type: str) -> Any:
    """
    Get the ID of an entity record.

    Args:
        entity: The entity record
        entity_type: The type of entity

    Returns:
        The record's ID field (term_id for ontology terms, otherwise _id)
    """
    return entity.get(ID_FIELDS.get(entity_type, '_id'))


def name_matches(entity: dict[str, Any], entity_type: str, name: str) -> bool:
    """
    Check whether an entity's name, or one of its other names, equals a name case-insensitively.

    Args:
        entity: The entity record
        entity_type: The type of entity, which selects the fields compared (see NAME_FIELDS)
        name: The name to compare

    Returns:
        Whether the entity matches the name exactly
    """
    target = name.strip().casefold()
    for field in NAME_FIELDS.get(entity_type, ['name']):
        value = entity.get(field)
        for candidate in value if isinstance(value, list) else [value]:
            if isinstance(candidate, str) and candidate.casefold() == target:
                return True
    return False


def name_not_found(entity_type: str, name: str, near_matches: list[dict[str, Any]] | None = None) -> str:
    """
    Describe a name without exact matches, suggesting the entities the name search returned instead.

    Args:
        entity_type: The type of entity
        name: The name looked up
        near_matches: Entities the name search returned that do not match exactly

    Returns:
        Message such as "No gene found with symbol 'LIVER'. Did you mean: LIVAR?"
    """
    label = TYPE_LABELS.get(entity_type, entity_type)
    message = f"No {label} found with {'symbol' if entity_type == 'gene' else 'name'} '{name}'"
    suggestions: list[str] = []
    for entity in near_matches or []:
        suggestion = entity.get('name')
        if entity_type != 'gene' and entity_id(entity, entity_type):
            suggestion = f'{suggestion} ({entity_id(entity, entity_type)})'
        if suggestion and suggestion not in suggestions:
            suggestions.append(suggestion)
    if suggestions:
        more = ', …' if len(suggestions) > MAX_SUGGESTIONS else ''
        message += f". Did you mean: {', '.join(suggestions[:MAX_SUGGESTIONS])}{more}?"
    return message


def with_article(noun: str) -> str:
    """
    Prefix a noun with its indefinite article.

    Args:
        noun: The noun, e.g. "ontology term"

    Returns:
        The noun with "a" or "an"
    """
    return f"{'an' if noun[:1] in 'aeiou' else 'a'} {noun}"


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
        # Ontology terms (e.g. MONDO_0007915, HP:0033726, NCIT_C27153, Orphanet_586)
        (ONTOLOGY_TERM, 'ontology', 'term_id'),
        # Drugs
        (r'^PA\d+$', 'drug', 'drug_id'),
        # Complexes
        (r'^CPX-\d+$', 'complex', 'complex_id'),
        # Studies
        (r'^GCST\d+$', 'study', 'study_id'),
        # Pathways
        (r'^R-[A-Z]{3}-\d+$', 'pathway', 'id'),
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
            ValueError: If the identifier is blank or its format is not recognized, the hint is unknown, or the
                identifier is an ID of a different type than the hint (strings shaped like gene symbols count as names)
        """
        # Normalize identifier
        identifier = identifier.strip()
        if not identifier:
            raise ValueError('The identifier is empty. Provide an ID or a name.')

        # A hint selects the entity type; identifiers that are not IDs of that type are looked up by name
        if hint:
            hinted_type = HINT_TYPES.get(hint.lower())
            if hinted_type is None:
                raise ValueError(f"Unknown hint: '{hint}'. Valid hints: {', '.join(HINT_TYPES)}")
            for pattern, entity_type, param_name in cls.PATTERNS:
                if entity_type == hinted_type and param_name != 'name' and re.match(pattern, identifier, re.IGNORECASE):
                    return entity_type, param_name  # type: ignore
            if not re.match(ID_SHAPED_SYMBOL, identifier, re.IGNORECASE):
                for pattern, entity_type, param_name in cls.PATTERNS:
                    if param_name != 'name' and re.match(pattern, identifier, re.IGNORECASE):
                        expected = 'name' if hinted_type in NAME_PARAMS else 'ID'
                        raise ValueError(
                            f"'{identifier}' is {with_article(TYPE_LABELS.get(entity_type, entity_type))} ID, "
                            f'not {with_article(hint.lower())} {expected}.'
                        )
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
    async def identify(cls, identifier: str, hint: str | None = None) -> Identification:
        """
        Detect the entity type of an identifier and normalize it for API queries.

        Gene symbols only match genes whose symbol equals them case-insensitively, so they are looked up
        across all pages and the exact matches are returned, with the symbol in the catalog's case (e.g.
        C1orf112). Without a hint, an identifier that fits both another ID pattern and ID_SHAPED_SYMBOL (e.g.
        RS1, CA1 or P2RY12) is a gene if a gene with exactly that symbol exists. Either check costs one gene
        name lookup.

        Args:
            identifier: The ID string to parse
            hint: Optional hint about the entity type

        Returns:
            The Identification, with the exact and near matches of a gene symbol

        Raises:
            ValueError: As detect_entity_type
        """
        entity_type, param_name = cls.detect_entity_type(identifier, hint)
        normalized_id = cls.normalize_identifier(identifier, entity_type, param_name)

        is_symbol = (entity_type, param_name) == ('gene', 'name')
        ambiguous = hint is None and not is_symbol and re.match(ID_SHAPED_SYMBOL, identifier.strip(), re.IGNORECASE)
        if is_symbol or ambiguous:
            symbol = identifier.strip().upper()
            matches, near_matches = await cls.lookup_name('gene', symbol)
            if matches:
                symbol = matches[0].get('name') or symbol
            if is_symbol or matches:
                return Identification('gene', 'name', symbol, matches, near_matches)

        return Identification(entity_type, param_name, normalized_id)  # type: ignore

    @classmethod
    async def lookup_name(cls, entity_type: EntityType, name: str) -> tuple[list[dict], list[dict]]:
        """
        Look up entities by name across all pages, and split them into exact and near matches.

        The name is searched with each lookup parameter of NAME_LOOKUP_PARAMS (e.g. name and synonyms for
        ontology terms) concurrently, and the candidates are merged by ID. The catalog's searches are fuzzy
        (e.g. LIVER finds LIVAR); only entities whose name, or another name field (see NAME_FIELDS), equals the
        name case-insensitively match exactly.

        Args:
            entity_type: The type of entity, which must have a name lookup (see NAME_PARAMS)
            name: The normalized name

        Returns:
            Tuple of (exact matches, other entities the searches returned)

        Raises:
            ValueError: If the name is blank, which the API would treat as no filter
        """
        if not name.strip():
            raise ValueError('The name is empty. Provide a name to look up.')
        results = await asyncio.gather(
            *(cls.lookup_all(entity_type, param_name, name) for param_name in NAME_LOOKUP_PARAMS[entity_type])
        )
        entities: list[dict] = []
        seen_ids = set()
        for entity in (entity for result in results for entity in result):
            key = entity_id(entity, entity_type)
            if key is None or key not in seen_ids:
                seen_ids.add(key)
                entities.append(entity)
        exact = [entity for entity in entities if name_matches(entity, entity_type, name)]
        near = [entity for entity in entities if not name_matches(entity, entity_type, name)]
        return exact, near

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

        Separators are stored as underscores, prefixes in their canonical case (e.g. NCBITaxon_, VariO_,
        Orphanet_; see ONTOLOGY_PREFIXES) and local IDs in uppercase.

        Args:
            term_id: The stripped term ID

        Returns:
            Normalized term ID
        """
        match = re.match(ONTOLOGY_TERM, term_id, re.IGNORECASE)
        if match is None:
            return term_id.upper().replace(':', '_')
        prefix, local_id = match.groups()
        return f'{ONTOLOGY_PREFIX_CASE[prefix.lower()]}_{local_id.upper()}'
