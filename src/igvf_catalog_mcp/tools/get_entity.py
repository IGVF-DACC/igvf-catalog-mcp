"""Get entity tool - universal entity lookup with auto-detection."""

from typing import Any

from mcp.types import TextContent, Tool

from ..services.api_client import get_client
from ..services.formatter import ToolError, add_entity_type, format_error
from ..services.id_parser import IDParser

# Tool definition
GET_ENTITY_TOOL = Tool(
    name='igvf_catalog_get_entity',
    description=(
        'Look up any biological entity by ID with automatic type detection. '
        'Supports genes (BRCA1, ENSG00000139618), variants (rs12345, NC_000017.11:43044295:G:A), '
        'proteins (ENSP00000493376, P49711), transcripts (ENST00000443707), '
        'diseases (Orphanet_586, MONDO_0008199), drugs (PA448497), '
        'complexes (CPX-9), and more. '
        'Returns detailed information about the entity.'
    ),
    inputSchema={
        'type': 'object',
        'properties': {
            'id': {
                'type': 'string',
                'description': "Entity identifier (e.g., 'BRCA1', 'rs12345', 'ENSG00000139618')",
            },
            'hint': {
                'type': 'string',
                'description': (
                    'Optional entity type. With a gene, protein, disease, drug or complex hint, an identifier '
                    "that is not an ID of that type is looked up by name (e.g. 'CTCF' with hint 'protein')."
                ),
                'enum': ['gene', 'variant', 'protein', 'transcript', 'disease', 'drug', 'complex'],
            },
        },
        'required': ['id'],
    },
)


async def get_entity(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute the get_entity tool.

    Args:
        arguments: Tool arguments with 'id' and optional 'hint'

    Returns:
        List of TextContent with entity information or error message
    """
    try:
        entity_id = arguments['id']
        hint = arguments.get('hint')

        # Detect entity type and normalize the identifier
        entity_type, param_name, normalized_id = await IDParser.identify(entity_id, hint)

        # Query the API
        entities = await get_client().call(
            IDParser.get_client_method(entity_type),
            **{param_name: normalized_id, 'page': 0},
        )

        # Format response
        if not entities:
            return [
                TextContent(
                    type='text',
                    text=f"No {entity_type} found with {param_name}='{normalized_id}'",
                )
            ]

        # Add entity type to results
        results = [add_entity_type(entity, entity_type) for entity in entities]

        # Format as JSON
        import json
        response_text = json.dumps(results, indent=2)

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
