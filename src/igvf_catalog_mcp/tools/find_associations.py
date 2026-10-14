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
from ..services.formatter import ToolError, build_pagination_metadata, format_error
from ..services.id_parser import IDParser, name_not_found
from ..services.id_parser import entity_id as node_id

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
            'hint': {
                'type': 'string',
                'description': (
                    'Optional entity type of entity_id. With a gene, protein, disease, drug or complex hint, '
                    "an identifier that is not an ID of that type is used as a name (e.g. 'lupus' with hint "
                    "'disease'). Names are resolved to the entities whose name (or synonym) matches exactly, listed "
                    'in resolved_entities, and associations are queried by their IDs. '
                    "Also selects the type of IDs that fit several, e.g. 'P2RY12' with hint 'protein'."
                ),
                'enum': ['gene', 'variant', 'protein', 'transcript', 'disease', 'drug', 'complex'],
            },
            'relationship': {
                'type': 'string',
                'description': 'Type of relationship to find',
                'enum': list(RELATIONSHIP_TYPE_MAPPING.keys()) + ['all'],
            },
            'filters': {
                'type': 'object',
                'description': (
                    'Optional filters. Each endpoint supports a different set of filters and values (see '
                    'list_sources); query_metadata lists the filters_not_applied to each endpoint, with the reason.'
                ),
                'properties': {
                    'p_value': {'type': 'number', 'description': 'Maximum p-value threshold'},
                    'source': {
                        'type': 'string',
                        'description': "Data source (e.g., 'AFGR', 'EBI', 'IGVF'); list_sources lists the valid values",
                    },
                    'biological_context': {'type': 'string', 'description': 'Tissue or cell type'},
                    'method': {
                        'type': 'string',
                        'description': "Experimental method (e.g., 'eQTL', 'CRISPR screen', 'ENCODE-rE2G', 'GWAS')",
                    },
                    'label': {'type': 'string', 'description': "Edge label/type (e.g., 'eQTL', 'GWAS')"},
                    'score': {
                        'type': 'number',
                        'description': 'Minimum score (e.g. E2G prediction score, for gene-genomic element queries)',
                    },
                    'r2': {'type': 'number', 'description': 'LD r2 threshold (for LD queries)'},
                    'd_prime': {'type': 'number', 'description': 'LD D\' threshold (for LD queries)'},
                    'ancestry': {'type': 'string', 'description': 'Population ancestry (for LD queries)'},
                },
            },
            'limit': {
                'type': 'integer',
                'description': (
                    'Maximum results per data source (endpoint); with several endpoints, '
                    'up to limit × endpoints rows (default: 25). Some endpoints have a lower maximum page size '
                    '(see max_limit in list_sources); query_metadata reports limit_capped_to when it applies.'
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
    'term_id': ['phenotype_id', 'disease_id'],
    'protein_id': ['query'],
    'dbxrefs': ['query'],
}

# Identifiers resolved through a node lookup: (entity type, lookup parameter) -> (parameter of the resolved values,
# field of the looked-up node holding them). Names are always resolved, to the exact matches' IDs, so edges are queried
# by ID. Other identifiers are resolved only for endpoints that do not accept them (e.g. per allele of an rsID). The
# resolved parameter is mapped to the endpoint's parameter like an identifier (see EDGE_PARAM_ALIASES).
RESOLVED_EDGE_PARAMS: dict[tuple[str, str], tuple[str, str]] = {
    ('variant', 'rsid'): ('spdi', 'spdi'),
    ('protein', 'dbxrefs'): ('uniprot_name', 'uniprot_names'),
    ('gene', 'name'): ('gene_id', '_id'),
    ('protein', 'name'): ('protein_id', '_id'),
    ('ontology', 'name'): ('term_id', 'term_id'),
    ('drug', 'name'): ('drug_id', '_id'),
    ('complex', 'name'): ('complex_id', '_id'),
}


# Filters whose value must be in a list of the endpoint configuration: filter name -> configuration key
VALUE_LIST_FILTERS: dict[str, str] = {'source': 'sources', 'method': 'methods', 'label': 'labels'}

# Range filters for which a plain number is a minimum
MIN_THRESHOLD_FILTERS = ['r2', 'd_prime', 'z_score', 'score']

NOT_SUPPORTED = 'not supported by this endpoint'


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
) -> tuple[dict[str, Any], dict[str, str]]:
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
        Tuple of (query parameters, user filters not applied to this endpoint mapped to the reason)
    """
    accepted_params = method_params(edge_config['client_method'])
    params = {
        param_name: entity_id,
        'limit': min(limit, edge_config.get('max_limit', 500)),
        'page': page,
    }
    not_applied: dict[str, str] = {}

    # Add verbose mode if supported
    if verbose and 'verbose' in accepted_params:
        params['verbose'] = 'true'

    # Process filters based on endpoint configuration
    supported_filters = edge_config.get('filters', {})

    for filter_name, filter_value in user_filters.items():
        if filter_name == 'p_value':
            # User provides max p-value, API expects min -log10(p-value)
            if 'neg_log10_pvalue' not in supported_filters:
                not_applied[filter_name] = NOT_SUPPORTED
            elif not isinstance(filter_value, (int, float)) or filter_value <= 0:
                not_applied[filter_name] = 'invalid value; must be a number greater than 0'
            else:
                params['neg_log10_pvalue'] = f'gte:{-math.log10(filter_value):.2f}'
            continue

        if filter_name in VALUE_LIST_FILTERS:
            # Source, method and label values must be one of the endpoint's values
            allowed = edge_config.get(VALUE_LIST_FILTERS[filter_name], [])
            if filter_name not in accepted_params or not allowed:
                not_applied[filter_name] = NOT_SUPPORTED
            elif filter_value not in allowed:
                not_applied[filter_name] = f"invalid value; valid: {', '.join(allowed)}"
            else:
                params[filter_name] = filter_value
            continue

        if filter_name not in supported_filters:
            not_applied[filter_name] = NOT_SUPPORTED
            continue

        filter_type = supported_filters[filter_name]

        if filter_type == 'range':
            if filter_name in MIN_THRESHOLD_FILTERS and not (isinstance(filter_value, str) and ':' in filter_value):
                # Numbers are minimum thresholds
                params[filter_name] = f'gte:{filter_value}'
            else:
                # Generic range filter, either a plain value or an operator string like "gte:0.5"
                params[filter_name] = str(filter_value)
        elif filter_type in ['string', 'enum']:
            # Direct string/enum filters
            params[filter_name] = filter_value

    return params, not_applied


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
        hint = arguments.get('hint')

        if relationship not in RELATIONSHIP_TYPE_MAPPING and relationship != 'all':
            raise ToolError(
                f'Unknown relationship type: {relationship}. '
                f"Valid types: {', '.join(RELATIONSHIP_TYPE_MAPPING.keys())}, all"
            )

        # Detect entity type and normalize the identifier
        entity_type, param_name, normalized_id, nodes, near_matches = await IDParser.identify(entity_id, hint)

        # Determine which endpoints to query
        if relationship == 'all':
            # Get all applicable relationship types for this entity
            endpoint_keys = []
            for rel_type, entity_map in RELATIONSHIP_TYPE_MAPPING.items():
                if entity_type in entity_map:
                    endpoint_keys.extend(entity_map[entity_type])
        else:
            # Get endpoints for specific relationship type
            endpoint_keys = get_endpoints_for_entity_and_relationship(
                entity_type, relationship)

            if not endpoint_keys:
                raise ToolError(f"Relationship type '{relationship}' not applicable to {entity_type} entities.")

        # Names are resolved to the IDs of the entities that match them exactly
        resolved_entities = None
        if param_name == 'name':
            if nodes is None:
                nodes, near_matches = await IDParser.lookup_name(entity_type, normalized_id)
            if not nodes:
                return [TextContent(type='text', text=name_not_found(entity_type, normalized_id, near_matches))]
            resolved_entities = [{'id': node_id(node, entity_type), 'name': node.get('name')} for node in nodes]

        # Query all applicable endpoints
        all_associations = []
        query_metadata = []

        client = get_client()
        resolved_ids: list[str] | None = None
        resolution = RESOLVED_EDGE_PARAMS.get((entity_type, param_name))
        for endpoint_key in endpoint_keys:
            edge_config = get_edge_config(endpoint_key)
            if not edge_config:
                continue

            # The IDParser gives us the node lookup parameter, but each endpoint may expect a different name
            endpoint_param_name = resolve_edge_param(param_name, edge_config)
            resolve = False
            if endpoint_param_name is None and resolution is not None:
                endpoint_param_name = resolve_edge_param(resolution[0], edge_config)
                resolve = endpoint_param_name is not None
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
                if resolve:
                    field = resolution[1]
                    if resolved_ids is None:
                        if nodes is None:
                            nodes = await IDParser.lookup_all(entity_type, param_name, normalized_id)
                        resolved_ids = []
                        for node in nodes:
                            value = node.get(field) or []
                            for resolved_id in value if isinstance(value, list) else [value]:
                                if resolved_id not in resolved_ids:
                                    resolved_ids.append(resolved_id)
                    lookup_ids = resolved_ids
                else:
                    lookup_ids = [normalized_id]

                params, filters_not_applied = build_query_params(
                    normalized_id, endpoint_param_name, edge_config, filters, limit, verbose, page
                )

                # Query the endpoint
                associations = []
                has_more = False
                effective_limit = min(limit, edge_config.get('max_limit', 500))
                for lookup_id in lookup_ids:
                    rows = await client.call(edge_config['client_method'], **{**params, endpoint_param_name: lookup_id})
                    has_more = has_more or len(rows) >= effective_limit
                    associations.extend(rows)

                # Add metadata to each association
                for assoc in associations:
                    assoc['_endpoint'] = endpoint_key
                    assoc['_endpoint_path'] = edge_config['path']

                all_associations.extend(associations)

                metadata = {
                    'endpoint': endpoint_key,
                    'path': edge_config['path'],
                    'results_count': len(associations),
                    '_pagination': build_pagination_metadata(associations, page, effective_limit, has_more),
                    'params_used': {k: v for k, v in params.items() if k not in ['page']},
                }
                if limit > effective_limit:
                    metadata['limit_capped_to'] = effective_limit
                if filters_not_applied:
                    metadata['filters_not_applied'] = filters_not_applied
                if resolve:
                    metadata['resolved_from'] = param_name
                    metadata['params_used'][endpoint_param_name] = lookup_ids
                    if not lookup_ids:
                        metadata['note'] = (
                            f"No {entity_type} found with {param_name}='{normalized_id}', "
                            'so this endpoint was not queried.'
                        )
                query_metadata.append(metadata)

            except Exception as e:
                # Log error but continue with other endpoints
                query_metadata.append(
                    {
                        'endpoint': endpoint_key,
                        'path': edge_config['path'],
                        'error': str(e),
                    }
                )

        if query_metadata and all('error' in m for m in query_metadata):
            errors = '; '.join(f"{m['endpoint']}: {m['error']}" for m in query_metadata)
            raise ToolError(f'Error finding associations: {errors}')

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

        queried = [m for m in query_metadata if 'params_used' in m]
        unused_filters = [
            name for name in filters if queried and all(name in m.get('filters_not_applied', {}) for m in queried)
        ]

        response_data = {
            '_pagination': top_pagination,
            'entity_id': normalized_id,
            'entity_type': entity_type,
            **({'resolved_entities': resolved_entities} if resolved_entities is not None else {}),
            'relationship_type': relationship,
            'num_associations': len(all_associations),
            'query_metadata': query_metadata,
            'associations': all_associations,
        }
        if unused_filters:
            response_data['note'] = (
                f"Filters not applied to any endpoint: {', '.join(unused_filters)}. "
                'See filters_not_applied in query_metadata for the reasons, and list_sources for valid values.'
            )

        response_text = json.dumps(response_data, indent=2)

        return [
            TextContent(
                type='text',
                text=response_text,
            )
        ]

    except ToolError:
        raise
    except ValueError as e:
        # ID parsing errors
        raise ToolError(format_error(e)) from e
    except Exception as e:
        # API errors or other issues
        raise ToolError(f'Error finding associations: {format_error(e)}') from e
