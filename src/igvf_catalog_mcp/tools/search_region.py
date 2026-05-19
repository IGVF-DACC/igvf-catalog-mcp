"""Search region tool - find entities in a genomic region."""

import asyncio
import json
from typing import Any

from mcp.types import Tool, TextContent

from ..services.api_client import IGVFCatalogClient
from ..services.region_parser import RegionParser
from ..services.formatter import format_error, build_pagination_metadata


# Tool definition
SEARCH_REGION_TOOL = Tool(
    name='igvf_catalog_search_region',
    description=(
        'Find all biological entities within a genomic region. '
        'Searches genes, variants, and regulatory elements in parallel. '
        "Supports flexible region formats: 'chr1:1000-2000', '1:1M-2M', 'chrX:1,000,000-2,000,000'. "
        'Returns genes, variants, and regulatory elements found in the region. '
        'Supports pagination — check _pagination.has_more in the response and use the page parameter to retrieve additional results.'
    ),
    inputSchema={
        'type': 'object',
        'properties': {
            'region': {
                'type': 'string',
                'description': "Genomic region (e.g., 'chr1:1000000-2000000' or '1:1M-2M')",
            },
            'include': {
                'type': 'array',
                'items': {'type': 'string', 'enum': ['genes', 'variants', 'regulatory_elements']},
                'description': 'Entity types to include (default: all)',
            },
            'organism': {
                'type': 'string',
                'description': 'Organism name',
                'enum': ['Homo sapiens', 'Mus musculus'],
                'default': 'Homo sapiens',
            },
            'limit': {
                'type': 'integer',
                'description': 'Maximum results per entity type (default: 25)',
                'minimum': 1,
                'maximum': 500,
                'default': 25,
            },
            'page': {
                'type': 'integer',
                'description': 'Page number (0-indexed). Use when previous results indicated more data is available.',
                'minimum': 0,
                'default': 0,
            },
        },
        'required': ['region'],
    },
)


async def search_region(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute the search_region tool.

    Args:
        arguments: Tool arguments with 'region' and optional filters

    Returns:
        List of TextContent with entities found in the region
    """
    try:
        region_str = arguments['region']
        include = arguments.get(
            'include', ['genes', 'variants', 'regulatory_elements'])
        organism = arguments.get('organism', 'Homo sapiens')
        limit = arguments.get('limit', 25)
        page = arguments.get('page', 0)

        # Parse and validate the region
        region = RegionParser.parse_region(region_str)

        # Warn if region is very large (> 10 Mb)
        region_size = region.end - region.start
        if region_size > 10_000_000:
            warning = f'Warning: Large region ({region_size:,} bp). Results may be incomplete.\n\n'
        else:
            warning = ''

        # Build queries for different entity types
        queries = {}

        if 'genes' in include:
            queries['genes'] = ('/api/genes', str(region))

        if 'variants' in include:
            queries['variants'] = ('/api/variants', str(region))

        if 'regulatory_elements' in include:
            queries['regulatory_elements'] = (
                '/api/genomic-elements', str(region))

        # Execute queries in parallel
        async with IGVFCatalogClient() as client:
            tasks = {
                entity_type: client.search_region(
                    endpoint=endpoint,
                    region_str=region_str_query,
                    organism=organism,
                    limit=limit,
                    page=page,
                )
                for entity_type, (endpoint, region_str_query) in queries.items()
            }

            results = await asyncio.gather(*tasks.values(), return_exceptions=True)

            # Combine results with per-type pagination metadata
            response = {}
            for entity_type, result in zip(tasks.keys(), results):
                if isinstance(result, Exception):
                    response[entity_type] = {'error': str(result)}
                else:
                    response[entity_type] = {
                        '_pagination': build_pagination_metadata(result, page, limit),
                        'items': result,
                    }

        # Format response
        any_has_more = any(
            v.get('_pagination', {}).get('has_more', False)
            for v in response.values()
            if isinstance(v, dict) and 'error' not in v
        )
        top_pagination = {
            'current_page': page,
            'limit': limit,
            'has_more': any_has_more,
        }
        if any_has_more:
            top_pagination['next_page'] = page + 1
            top_pagination['note'] = f'More results available. Call again with page={page + 1} to continue.'

        response_data = {
            '_pagination': top_pagination,
            'region': str(region),
            'region_size_bp': region_size,
            'organism': organism,
            'results': response,
        }

        response_text = warning + json.dumps(response_data, indent=2)

        return [
            TextContent(
                type='text',
                text=response_text,
            )
        ]

    except ValueError as e:
        # Region parsing errors
        return [
            TextContent(
                type='text',
                text=format_error(e),
            )
        ]
    except Exception as e:
        # API errors or other issues
        return [
            TextContent(
                type='text',
                text=f'Error searching region: {format_error(e)}',
            )
        ]
