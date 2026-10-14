"""Find associations tool - discover relationships between entities."""

import json
import math
from typing import Any

from mcp.types import TextContent, Tool

from ..services.api_client import get_client, method_params
from ..services.edge_config import (
    RELATIONSHIP_TYPE_MAPPING,
    get_edge_config,
    get_endpoints_for_entity_and_relationship,
)
from ..services.formatter import build_pagination_metadata, format_error
from ..services.id_parser import IDParser

# Tool definition
FIND_ASSOCIATIONS_TOOL = Tool(
    name='igvf_catalog_find_associations',
    description=(
        'Find connections between entities in the knowledge graph. '
        'Discovers eQTLs, GWAS associations, protein interactions, pathways, and more. '
        "Relationship types: 'regulatory' (eQTLs, enhancer-gene), 'genetic' (GWAS, disease-gene), "
        "'physical' (protein-protein), 'functional' (pathways, GO terms), 'pharmacological' (drug-variant), "
        "'ld' (linkage disequilibrium), 'coding' (coding variant effects), 'transcription' (gene-transcript-protein). "
        'Returns detailed associations with p-values, effect sizes, and sources. '
        'The limit applies to each data source (endpoint) separately, so a relationship backed by several '
        'endpoints can return up to limit × endpoints associations; query_metadata lists the per-endpoint counts. '
        'Supports pagination — check _pagination.has_more in the response and use the page parameter '
        'to retrieve additional results.'
    ),
    inputSchema={
        'type': 'object',
        'properties': {
            'entity_id': {
                'type': 'string',
                'description': "Starting entity ID (e.g., 'TP53', 'rs12345', 'ENSG00000141510')",
            },
            'relationship': {
                'type': 'string',
                'description': 'Type of relationship to find',
                'enum': list(RELATIONSHIP_TYPE_MAPPING.keys()) + ['all'],
            },
            'filters': {
                'type': 'object',
                'description': 'Optional filters',
                'properties': {
                    'p_value': {'type': 'number', 'description': 'Maximum p-value threshold'},
                    'source': {'type': 'string', 'description': "Data source (e.g., 'AFGR', 'EBI eQTL Catalogue')"},
                    'biological_context': {'type': 'string', 'description': 'Tissue or cell type'},
                    'method': {'type': 'string', 'description': 'Experimental method'},
                    'label': {'type': 'string', 'description': 'Edge label/type'},
                    'r2': {'type': 'number', 'description': 'LD r2 threshold (for LD queries)'},
                    'd_prime': {'type': 'number', 'description': 'LD D\' threshold (for LD queries)'},
                    'ancestry': {'type': 'string', 'description': 'Population ancestry (for LD queries)'},
                },
            },
            'limit': {
                'type': 'integer',
                'description': (
                    'Maximum results per data source (endpoint); with several endpoints, '
                    'up to limit × endpoints rows (default: 25)'
                ),
                'minimum': 1,
                'maximum': 500,
                'default': 25,
            },
            'verbose': {
                'type': 'boolean',
                'description': 'Return full entity details (default: false)',
                'default': False,
            },
            'page': {
                'type': 'integer',
                'description': 'Page number (0-indexed). Use when previous results indicated more data is available.',
                'minimum': 0,
                'default': 0,
            },
        },
        'required': ['entity_id', 'relationship'],
    },
)


# Edge parameter names to try when an endpoint does not accept the node lookup parameter
EDGE_PARAM_ALIASES: dict[str, list[str]] = {
    'name': ['gene_name'],
    'term_id': ['phenotype_id', 'disease_id'],
    'protein_id': ['query'],
    'dbxrefs': ['query'],
}


def resolve_edge_param(param_name: str, edge_config: dict[str, Any]) -> str | None:
    """
    Map an IDParser parameter name to the parameter an edge endpoint accepts.

    Args:
        param_name: Parameter name from IDParser (e.g., "name", "rsid", "term_id")
        edge_config: The edge endpoint configuration

    Returns:
        The endpoint's parameter name, or None if the identifier type is not supported
    """
    from_params = edge_config.get('from_params', [])
    for candidate in [param_name, *EDGE_PARAM_ALIASES.get(param_name, [])]:
        if candidate in from_params:
            return candidate
    return None


def build_query_params(
    entity_id: str,
    param_name: str,
    edge_config: dict[str, Any],
    user_filters: dict[str, Any],
    limit: int,
    verbose: bool,
    page: int = 0,
) -> dict[str, Any]:
    """
    Build query parameters for an edge endpoint based on its configuration.

    Parameter names are the API's query parameter names, which are also the
    keyword arguments of the generated client method.

    Args:
        entity_id: The normalized entity identifier
        param_name: The parameter name for this entity type at this endpoint
        edge_config: The edge endpoint configuration
        user_filters: User-provided filters
        limit: Result limit
        verbose: Whether to request verbose output
        page: Page number (0-indexed)

    Returns:
        Dictionary of query parameters
    """
    accepted_params = method_params(edge_config['client_method'])
    params = {
        param_name: entity_id,
        'limit': min(limit, edge_config.get('max_limit', 500)),
        'page': page,
    }

    # Add verbose mode if supported
    if verbose and 'verbose' in accepted_params:
        params['verbose'] = 'true'

    # Process filters based on endpoint configuration
    supported_filters = edge_config.get('filters', {})

    for filter_name, filter_value in user_filters.items():
        if filter_name == 'p_value':
            # User provides max p-value, API expects min -log10(p-value)
            if 'neg_log10_pvalue' in supported_filters and filter_value > 0:
                params['neg_log10_pvalue'] = f'gte:{-math.log10(filter_value):.2f}'
            continue

        if filter_name not in supported_filters:
            continue

        filter_type = supported_filters[filter_name]

        if filter_type == 'range':
            if filter_name in ['r2', 'd_prime', 'z_score']:
                # These are typically min thresholds
                params[filter_name] = f'gte:{filter_value}'
            else:
                # Generic range filter, either a plain value or an operator string like "gte:0.5"
                params[filter_name] = str(filter_value)
        elif filter_type in ['string', 'enum']:
            # Direct string/enum filters
            params[filter_name] = filter_value

    # Validate and add source, method and label filters
    for filter_name, allowed_key in [('source', 'sources'), ('method', 'methods'), ('label', 'labels')]:
        if filter_name not in user_filters or filter_name not in accepted_params:
            continue
        if user_filters[filter_name] in edge_config.get(allowed_key, []):
            params[filter_name] = user_filters[filter_name]

    return params


async def find_associations(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute the find_associations tool.

    Args:
        arguments: Tool arguments with entity_id, relationship, and optional filters

    Returns:
        List of TextContent with associations found
    """
    try:
        entity_id = arguments['entity_id']
        relationship = arguments['relationship']
        filters = arguments.get('filters', {})
        limit = arguments.get('limit', 25)
        verbose = arguments.get('verbose', False)
        page = arguments.get('page', 0)

        # Detect entity type
        entity_type, param_name = IDParser.detect_entity_type(entity_id)
        normalized_id = IDParser.normalize_identifier(entity_id, entity_type)

        # Determine which endpoints to query
        if relationship == 'all':
            # Get all applicable relationship types for this entity
            endpoint_keys = []
            for rel_type, entity_map in RELATIONSHIP_TYPE_MAPPING.items():
                if entity_type in entity_map:
                    endpoint_keys.extend(entity_map[entity_type])
        else:
            # Get endpoints for specific relationship type
            if relationship not in RELATIONSHIP_TYPE_MAPPING:
                return [
                    TextContent(
                        type='text',
                        text=f'Unknown relationship type: {relationship}. '
                        f"Valid types: {', '.join(RELATIONSHIP_TYPE_MAPPING.keys())}, all",
                    )
                ]

            endpoint_keys = get_endpoints_for_entity_and_relationship(
                entity_type, relationship)

            if not endpoint_keys:
                return [
                    TextContent(
                        type='text',
                        text=f"Relationship type '{relationship}' not applicable to {entity_type} entities.",
                    )
                ]

        # Query all applicable endpoints
        all_associations = []
        query_metadata = []

        client = get_client()
        for endpoint_key in endpoint_keys:
            edge_config = get_edge_config(endpoint_key)
            if not edge_config:
                continue

            # The IDParser gives us the node lookup parameter, but each endpoint may expect a different name
            endpoint_param_name = resolve_edge_param(param_name, edge_config)
            if endpoint_param_name is None:
                query_metadata.append(
                    {
                        'endpoint': endpoint_key,
                        'path': edge_config['path'],
                        'error': f"Identifier type '{param_name}' is not supported by this endpoint. "
                        f"Supported: {', '.join(edge_config.get('from_params', []))}",
                    }
                )
                continue

            # Build query parameters
            try:
                params = build_query_params(
                    normalized_id, endpoint_param_name, edge_config, filters, limit, verbose, page
                )

                # Query the endpoint
                associations = await client.call(edge_config['client_method'], **params)

                # Add metadata to each association
                for assoc in associations:
                    assoc['_endpoint'] = endpoint_key
                    assoc['_endpoint_path'] = edge_config['path']

                all_associations.extend(associations)

                effective_limit = min(limit, edge_config.get('max_limit', 500))
                query_metadata.append(
                    {
                        'endpoint': endpoint_key,
                        'path': edge_config['path'],
                        'results_count': len(associations),
                        '_pagination': build_pagination_metadata(associations, page, effective_limit),
                        'params_used': {k: v for k, v in params.items() if k not in ['page']},
                    }
                )

            except Exception as e:
                # Log error but continue with other endpoints
                query_metadata.append(
                    {
                        'endpoint': endpoint_key,
                        'path': edge_config['path'],
                        'error': str(e),
                    }
                )

        # Format response
        any_has_more = any(
            m.get('_pagination', {}).get('has_more', False)
            for m in query_metadata
        )
        top_pagination: dict[str, Any] = {
            'current_page': page,
            'limit': limit,
            'results_returned': len(all_associations),
            'has_more': any_has_more,
        }
        if any_has_more:
            top_pagination['next_page'] = page + 1
            top_pagination['note'] = f'More results available. Call again with page={page + 1} to continue.'

        response_data = {
            '_pagination': top_pagination,
            'entity_id': normalized_id,
            'entity_type': entity_type,
            'relationship_type': relationship,
            'num_associations': len(all_associations),
            'query_metadata': query_metadata,
            'associations': all_associations,
        }

        response_text = json.dumps(response_data, indent=2)

        return [
            TextContent(
                type='text',
                text=response_text,
            )
        ]

    except ValueError as e:
        # ID parsing errors
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
                text=f'Error finding associations: {format_error(e)}',
            )
        ]
