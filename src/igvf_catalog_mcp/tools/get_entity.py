"""Get entity tool - universal entity lookup with auto-detection."""

import json
from typing import Any

from mcp.types import TextContent, Tool

from ..services.api_client import get_client, method_params
from ..services.formatter import ToolError, add_entity_type, build_pagination_metadata, format_error
from ..services.id_parser import (
    API_PAGE_SIZE,
    DEFAULT_ORGANISM,
    ENTITY_MAX_LIMITS,
    MOUSE,
    ORGANISMS,
    IDParser,
    mouse_fallback,
    mouse_fallback_note,
    name_not_found,
    not_found,
    organism_params,
)

# Description of the organism argument of get_entity and resolve_id
ORGANISM_DESCRIPTION = (
    'Organism of genes, transcripts, proteins and variants (default: Homo sapiens); other entity types ignore it. '
    'Mouse Ensembl IDs (ENSMUSG, ENSMUST, ENSMUSP) are looked up in Mus musculus. Without an organism, a UniProt '
    'accession or protein name that matches no Homo sapiens protein is also looked up in Mus musculus.'
)

# Tool definition
GET_ENTITY_TOOL = Tool(
    name='igvf_catalog_get_entity',
    description=(
        'Look up any biological entity by ID with automatic type detection. '
        'Supports genes (BRCA1, HLA-A, ENSG00000139618), variants (rs12345, NC_000017.11:43044295:G:A), '
        'proteins (ENSP00000493376, P49711), transcripts (ENST00000443707), '
        'mouse genes, transcripts and proteins (ENSMUSG00000000001, Q9DC51; see organism), '
        'diseases (Orphanet_586, MONDO_0008199), drugs (PA448497), '
        'complexes (CPX-9), and more. '
        'Returns detailed information about the entity. '
        'Gene symbols match exactly (case-insensitive); other names (via hint) are searched and can match many '
        'entities: check _pagination.has_more in the response and use the page parameter to retrieve additional '
        'results.'
    ),
    inputSchema={
        'type': 'object',
        'properties': {
            'id': {
                'type': 'string',
                'description': "Entity identifier (e.g., 'BRCA1', 'rs12345', 'ENSG00000139618')",
                'minLength': 1,
            },
            'hint': {
                'type': 'string',
                'description': (
                    'Optional entity type. With a gene, protein, disease, drug or complex hint, an identifier '
                    "that is not an ID of that type is looked up by name (e.g. 'CTCF' with hint 'protein')."
                ),
                'enum': ['gene', 'variant', 'protein', 'transcript', 'disease', 'drug', 'complex'],
            },
            'organism': {
                'type': 'string',
                'description': ORGANISM_DESCRIPTION,
                'enum': ORGANISMS,
            },
            'limit': {
                'type': 'integer',
                'description': (
                    'Maximum number of results (default: 25). Each entity type has a maximum page size; '
                    '_pagination reports limit_capped_to when it applies. Complexes and studies have a fixed page '
                    'size of 25, reported as page_size.'
                ),
                'minimum': 1,
                'default': 25,
            },
            'page': {
                'type': 'integer',
                'description': 'Page number (0-indexed). Use when previous results indicated more data is available.',
                'minimum': 0,
                'default': 0,
            },
        },
        'required': ['id'],
    },
)


async def get_entity(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute the get_entity tool.

    Args:
        arguments: Tool arguments with 'id' and optional 'hint', 'organism', 'limit' and 'page'

    Returns:
        List of TextContent with entity information or error message
    """
    try:
        entity_id = arguments['id']
        hint = arguments.get('hint')
        limit = arguments.get('limit', 25)
        page = arguments.get('page', 0)
        organism = IDParser.lookup_organism(entity_id, arguments.get('organism'))

        # Detect entity type and normalize the identifier
        entity_type, param_name, normalized_id, matches, near_matches = await IDParser.identify(
            entity_id, hint, organism
        )

        fixed_page_size = False
        searched_mouse = False
        if matches is not None:
            # Gene symbols were looked up in full to keep only exact matches, so they are paged here
            if not matches:
                return [TextContent(type='text', text=name_not_found(entity_type, normalized_id, near_matches))]
            effective_limit = min(limit, ENTITY_MAX_LIMITS[entity_type])
            start = page * effective_limit
            entities = matches[start:start + effective_limit]
            has_more = len(matches) > start + effective_limit
        else:
            # Query the API; methods without a limit parameter return pages of the API's default size
            method_name = IDParser.get_client_method(entity_type)
            query = {param_name: normalized_id, 'page': page, **organism_params(entity_type, organism)}
            if 'limit' in method_params(method_name):
                effective_limit = min(limit, ENTITY_MAX_LIMITS[entity_type])
                query['limit'] = effective_limit
            else:
                effective_limit = API_PAGE_SIZE
                fixed_page_size = True
            entities = await get_client().call(method_name, **query)
            if not entities and page == 0 and mouse_fallback(entity_type, param_name, organism):
                entities = await get_client().call(method_name, **query, organism=MOUSE)
                searched_mouse = True
            has_more = None

        # Format response
        if not entities and page == 0:
            organisms = [DEFAULT_ORGANISM, MOUSE] if searched_mouse else [organism] if organism else None
            return [TextContent(type='text', text=not_found(entity_type, param_name, normalized_id, organisms))]

        pagination = build_pagination_metadata(entities, page, effective_limit, has_more)
        if fixed_page_size:
            pagination['limit'] = limit
            pagination['page_size'] = API_PAGE_SIZE
        elif limit > effective_limit:
            pagination['limit_capped_to'] = effective_limit

        response_data = {
            '_pagination': pagination,
            'entity_type': entity_type,
            'entities': [add_entity_type(entity, entity_type) for entity in entities],
        }
        if searched_mouse:
            response_data['note'] = mouse_fallback_note(entity_type, normalized_id, paged=True)
        if fixed_page_size:
            response_data['note'] = (
                f'{entity_type.capitalize()} lookups have a fixed page size of {API_PAGE_SIZE}, '
                'so limit does not apply.'
            )
        response_text = json.dumps(response_data, indent=2)

        return [
            TextContent(
                type='text',
                text=response_text,
            )
        ]

    except ValueError as e:
        # ID parsing or validation errors
        raise ToolError(format_error(e)) from e
    except Exception as e:
        # API errors or other issues
        raise ToolError(f'Error retrieving entity: {format_error(e)}') from e
