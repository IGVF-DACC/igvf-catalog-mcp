"""Response formatting utilities."""

from typing import Any


def build_pagination_metadata(results: list, page: int, limit: int) -> dict[str, Any]:
    """
    Build pagination metadata to include in tool responses.

    Uses a heuristic: if the number of results equals the limit,
    more pages likely exist.

    Args:
        results: The list of results returned from the API
        page: Current page number (0-indexed)
        limit: The limit used in the query

    Returns:
        Pagination metadata dict with has_more signal and next_page hint
    """
    has_more = len(results) >= limit
    meta: dict[str, Any] = {
        'current_page': page,
        'limit': limit,
        'results_returned': len(results),
        'has_more': has_more,
    }
    if has_more:
        meta['next_page'] = page + 1
        meta['note'] = f'More results available. Call again with page={page + 1} to continue.'
    return meta


def add_entity_type(entity: dict[str, Any], entity_type: str) -> dict[str, Any]:
    """
    Add _type field to an entity object.

    Args:
        entity: Entity dictionary
        entity_type: Type of entity

    Returns:
        Entity with _type field added
    """
    return {'_type': entity_type, **entity}


def format_error(error: Exception) -> str:
    """
    Format an error message in a user-friendly way.

    Args:
        error: Exception to format

    Returns:
        Formatted error message
    """
    error_type = type(error).__name__
    error_msg = str(error)

    # Add helpful context for common errors
    if 'Invalid region format' in error_msg:
        return f'{error_msg}\n\nExamples:\n- chr1:1000-2000\n- 1:1M-2M\n- chrX:1000000-2000000'

    if 'Could not detect entity type' in error_msg:
        return error_msg

    return f'{error_type}: {error_msg}'
