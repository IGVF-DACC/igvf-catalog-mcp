"""Resolve ID tool - convert between identifier formats."""

import json
import re
from typing import Any

from mcp.types import TextContent, Tool

from ..services.api_client import get_client
from ..services.formatter import ToolError, format_error
from ..services.id_parser import TYPE_LABELS, IDParser, name_not_found

# Tool definition
RESOLVE_ID_TOOL = Tool(
    name='igvf_catalog_resolve_id',
    description=(
        'Convert between different identifier formats and find all known aliases. '
        'Particularly useful for variants: converts between rsID, SPDI, HGVS, and ClinGen Allele Registry ID. '
        'Also works for genes (get all synonyms), proteins (UniProt, Ensembl), and other entities. '
        'Returns all known identifiers for the entity.'
    ),
    inputSchema={
        'type': 'object',
        'properties': {
            'id': {
                'type': 'string',
                'description': "Identifier to resolve (e.g., 'rs80357906', 'BRCA1', 'NC_000017.11:43044295:G:A')",
                'minLength': 1,
            },
            'target_type': {
                'type': 'string',
                'description': 'Preferred output format (optional)',
            },
        },
        'required': ['id'],
    },
)


def gnomad_af(variant: dict[str, Any]) -> float | None:
    """
    Get a variant's total gnomAD allele frequency.

    Args:
        variant: The variant record

    Returns:
        annotations.gnomad_af_total, or None if the variant has none
    """
    return (variant.get('annotations') or {}).get('gnomad_af_total')


def most_frequent_allele(variants: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    Pick the allele with the highest total gnomAD allele frequency.

    Args:
        variants: The alleles matching an identifier

    Returns:
        The most frequent allele, or None if no allele has gnomAD frequency data
    """
    with_af = [variant for variant in variants if gnomad_af(variant) is not None]
    return max(with_af, key=gnomad_af) if with_af else None


def on_primary_assembly(gene: dict[str, Any]) -> bool:
    """
    Check whether a gene is on a primary chromosome, rather than an alternate haplotype or the Y PAR copy.

    Args:
        gene: The gene record

    Returns:
        Whether the gene is on chr1-22, X, Y or M and is not a _PAR_Y copy
    """
    chromosome = gene.get('chr')
    return (
        isinstance(chromosome, str)
        and re.match(r'^chr([0-9]+|X|Y|M)$', chromosome) is not None
        and not str(gene.get('_id', '')).endswith('_PAR_Y')
    )


# Where a gene can be, in the order genes_on describes them, with the singular and plural phrase for each
GENE_LOCATIONS = [
    ('primary', 'on the primary assembly', 'on the primary assembly'),
    ('par_y', 'Y chromosome PAR copy', 'Y chromosome PAR copies'),
    ('alt', 'on an alternate haplotype', 'on alternate haplotypes'),
    ('fix', 'on a fix patch', 'on fix patches'),
    ('scaffold', 'on an unlocalized or unplaced scaffold', 'on unlocalized or unplaced scaffolds'),
    ('other', 'on another sequence', 'on other sequences'),
]


def gene_location(gene: dict[str, Any]) -> str:
    """
    Classify where a gene is.

    Args:
        gene: The gene record

    Returns:
        A key of GENE_LOCATIONS: primary, par_y, alt (alternate haplotype), fix (fix patch), scaffold (unlocalized
        or unplaced scaffold) or other
    """
    chromosome = str(gene.get('chr') or '')
    if on_primary_assembly(gene):
        return 'primary'
    if str(gene.get('_id', '')).endswith('_PAR_Y'):
        return 'par_y'
    if chromosome.endswith('_alt'):
        return 'alt'
    if chromosome.endswith('_fix'):
        return 'fix'
    if chromosome.endswith('_random') or chromosome.startswith('chrUn'):
        return 'scaffold'
    return 'other'


def genes_on(genes: list[dict[str, Any]]) -> str:
    """
    Count genes by where they are.

    Args:
        genes: The gene records

    Returns:
        Description such as "1 on the primary assembly and 6 on alternate haplotypes"
    """
    locations = [gene_location(gene) for gene in genes]
    parts = [
        f'{count} {singular if count == 1 else plural}'
        for key, singular, plural in GENE_LOCATIONS
        if (count := locations.count(key))
    ]
    return parts[0] if len(parts) == 1 else f"{', '.join(parts[:-1])} and {parts[-1]}"


def gene_preference(gene: dict[str, Any]) -> tuple[bool, bool, str]:
    """
    Sort key ranking the genes that share a symbol.

    Args:
        gene: The gene record

    Returns:
        Key preferring a gene on the primary assembly, then one with an HGNC ID, then the lowest gene ID
    """
    return not on_primary_assembly(gene), not gene.get('hgnc'), str(gene.get('_id', ''))


def gene_choice(genes: list[dict[str, Any]]) -> str:
    """
    Explain which rule of gene_preference picked the top-level gene among genes sharing a symbol.

    Args:
        genes: The gene records

    Returns:
        Reason such as "the only one on the primary assembly with an HGNC ID"
    """
    primary = [gene for gene in genes if on_primary_assembly(gene)]
    candidates = primary or genes
    scope = ' on the primary assembly' if primary else ''
    with_hgnc = [gene for gene in candidates if gene.get('hgnc')]
    if len(primary) == 1:
        reason = 'the only one on the primary assembly'
    elif len(with_hgnc) == 1:
        reason = f'the only one{scope} with an HGNC ID'
    elif with_hgnc:
        reason = f'the lowest gene ID of the {len(with_hgnc)}{scope} with an HGNC ID'
    else:
        reason = f'the lowest gene ID of the {len(candidates)}{scope}, none of which has an HGNC ID'
    return reason if primary else f'{reason}, as none is on the primary assembly'


def uniprot_accession(protein: dict[str, Any]) -> str | None:
    """
    Get a protein's UniProtKB accession.

    Args:
        protein: The protein record

    Returns:
        The UniProtKB (Swiss-Prot) accession from dbxrefs if present, otherwise the accession of its UniProt
        isoform IDs (e.g. P04637 for P04637-1) when they share one
    """
    for dbxref in protein.get('dbxrefs') or []:
        if isinstance(dbxref, dict) and dbxref.get('name') in ['UniProtKB', 'UniProtKB/Swiss-Prot', 'Swiss-Prot']:
            return dbxref.get('id')
    accessions = {uniprot_id.split('-')[0] for uniprot_id in protein.get('uniprot_ids') or []}
    return accessions.pop() if len(accessions) == 1 else None


async def resolve_id(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute the resolve_id tool.

    Args:
        arguments: Tool arguments with 'id' and optional 'target_type'

    Returns:
        List of TextContent with all identifiers for the entity
    """
    try:
        entity_id = arguments['id']

        # Detect entity type
        entity_type, param_name, normalized_id, matches, near_matches = await IDParser.identify(entity_id)

        # Query the API to get the full entity, and every allele of a variant or isoform of a protein
        if matches is not None:
            if not matches:
                return [TextContent(type='text', text=name_not_found(entity_type, normalized_id, near_matches))]
            entities = matches
        elif entity_type in ['variant', 'protein']:
            entities = await IDParser.lookup_all(entity_type, param_name, normalized_id)
        else:
            entities = await get_client().call(
                IDParser.get_client_method(entity_type), **{param_name: normalized_id, 'page': 0}
            )

        if not entities:
            return [
                TextContent(
                    type='text',
                    text=f"No {TYPE_LABELS.get(entity_type, entity_type)} found with {param_name}='{normalized_id}'",
                )
            ]

        if entity_type == 'variant':
            entity = most_frequent_allele(entities) or entities[0]
        elif entity_type == 'protein':
            entity = next((protein for protein in entities if protein.get('MANE_Select')), entities[0])
        elif entity_type == 'gene':
            entity = min(entities, key=gene_preference)
        else:
            entity = entities[0]

        # Extract identifiers based on entity type
        identifiers = {'input': entity_id, 'entity_type': entity_type}

        if entity_type == 'variant':
            # Variant identifiers
            identifiers['identifiers'] = {
                'rsid': entity.get('rsid'),
                'spdi': entity.get('spdi'),
                'hgvs': entity.get('hgvs'),
                'ca_id': entity.get('ca_id'),
                'variant_id': entity.get('_id'),
                'chromosome': entity.get('chr'),
                'position': entity.get('pos'),
                'ref': entity.get('ref'),
                'alt': entity.get('alt'),
            }
            identifiers['alleles'] = [
                {
                    **{key: variant.get(key) for key in ['spdi', 'hgvs', 'ca_id', 'ref', 'alt']},
                    'gnomad_af_total': gnomad_af(variant),
                }
                for variant in entities
            ]
            if len(entities) > 1:
                described = (
                    f"the allele with the highest gnomAD allele frequency ({entity.get('spdi')})"
                    if most_frequent_allele(entities)
                    else 'the first one, as no allele has gnomAD allele frequency data'
                )
                identifiers['note'] = (
                    f'{entity_id} is multi-allelic: it matches {len(entities)} variants, listed in alleles. '
                    f'The top-level identifiers describe {described}.'
                )
        elif entity_type == 'gene':
            # Gene identifiers
            identifiers['identifiers'] = {
                'gene_id': entity.get('_id'),
                'name': entity.get('name'),
                'hgnc': entity.get('hgnc'),
                'entrez': entity.get('entrez'),
                'synonyms': entity.get('synonyms', []),
                'chromosome': entity.get('chr'),
                'start': entity.get('start'),
                'end': entity.get('end'),
            }
            identifiers['genes'] = [
                {
                    'gene_id': gene.get('_id'),
                    'name': gene.get('name'),
                    'chromosome': gene.get('chr'),
                    'start': gene.get('start'),
                    'end': gene.get('end'),
                }
                for gene in entities
            ]
            if len(entities) > 1:
                identifiers['note'] = (
                    f'{entity_id} matches {len(entities)} genes, listed in genes: {genes_on(entities)}. '
                    f"The top-level identifiers describe {entity.get('_id')}, {gene_choice(entities)} (genes on the "
                    'primary assembly are preferred, then genes with an HGNC ID, then the lowest gene ID).'
                )
        elif entity_type == 'protein':
            # Protein identifiers
            dbxrefs = entity.get('dbxrefs') or []
            identifiers['identifiers'] = {
                'protein_id': entity.get('_id'),
                'name': entity.get('name'),
                'uniprot_ids': entity.get('uniprot_ids'),
                'uniprot_names': entity.get('uniprot_names'),
                'uniprot_full_names': entity.get('uniprot_full_names'),
                'uniprot_accession': uniprot_accession(entity),
                'MANE_Select': entity.get('MANE_Select'),
                'dbxrefs_count': len(dbxrefs),
            }
            identifiers['proteins'] = [
                {
                    'protein_id': protein.get('_id'),
                    **{key: protein.get(key) for key in ['name', 'uniprot_ids', 'uniprot_names', 'MANE_Select']},
                }
                for protein in entities
            ]
            if len(entities) > 1:
                mane_select = [protein for protein in entities if protein.get('MANE_Select')]
                if len(mane_select) > 1:
                    described = f"the first of the {len(mane_select)} MANE Select proteins ({entity.get('_id')})"
                elif mane_select:
                    described = f"the MANE Select protein ({entity.get('_id')})"
                else:
                    described = 'the first one, as none is MANE Select'
                identifiers['note'] = (
                    f'{entity_id} matches {len(entities)} proteins (e.g. isoforms), listed in proteins. '
                    f'The top-level identifiers describe {described}. get_entity returns the full records, '
                    'including all dbxrefs.'
                )
        elif entity_type == 'transcript':
            # Transcript identifiers
            identifiers['identifiers'] = {
                'transcript_id': entity.get('_id'),
                'chromosome': entity.get('chr'),
                'start': entity.get('start'),
                'end': entity.get('end'),
                'transcript_type': entity.get('transcript_type'),
            }
        elif entity_type == 'ontology':
            # Ontology term identifiers
            identifiers['identifiers'] = {
                'term_id': entity.get('term_id', entity.get('_id')),
                'name': entity.get('name'),
                'synonyms': entity.get('synonyms', []),
                'source': entity.get('source'),
            }
        else:
            # Generic identifiers
            identifiers['identifiers'] = {
                'id': entity.get('_id'),
                'name': entity.get('name'),
            }

        # Remove None values
        if 'identifiers' in identifiers:
            identifiers['identifiers'] = {
                k: v for k, v in identifiers['identifiers'].items() if v is not None
            }

        response_text = json.dumps(identifiers, indent=2)

        return [
            TextContent(
                type='text',
                text=response_text,
            )
        ]

    except ValueError as e:
        # ID parsing errors
        raise ToolError(format_error(e)) from e
    except Exception as e:
        # API errors or other issues
        raise ToolError(f'Error resolving identifier: {format_error(e)}') from e
