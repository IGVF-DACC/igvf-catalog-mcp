"""The IGVF Catalog OpenAPI spec that ships in the generated client package.

The generated client keeps only parameter names: enum query parameters become plain strings and page-size limits
appear only in docstrings. The processed spec the client was generated from has both, so endpoint paths, page sizes
and allowed parameter values are read from it instead of being copied by hand.
"""

import json
import re
from functools import cache
from importlib.resources import files
from typing import Any

CLIENT_PACKAGE = 'igvf_catalog_async_client'
SPEC_FILE = 'openapi_spec_processed.json'
# First igvf-catalog-async-client release that ships SPEC_FILE
MIN_CLIENT_VERSION = '1.3.0.post1'

HTTP_METHODS = {'get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace'}

# Each operation's description states its maximum page size: "The limit parameter controls the page size and can not
# exceed 100."
MAX_PAGE_SIZE = re.compile(r'can not exceed (\d+)')


class SpecError(RuntimeError):
    """The installed client's spec is missing or doesn't describe a client method."""


@cache
def load_spec() -> dict[str, Any]:
    """
    Load the processed OpenAPI spec shipped in the installed igvf-catalog-async-client.

    Returns:
        The spec

    Raises:
        SpecError: If the installed client doesn't ship the spec
    """
    resource = files(CLIENT_PACKAGE).joinpath(SPEC_FILE)
    if not resource.is_file():
        raise SpecError(
            f'The installed igvf-catalog-async-client does not include {SPEC_FILE}; it is too old. '
            f'Install igvf-catalog-async-client {MIN_CLIENT_VERSION} or later.'
        )
    return json.loads(resource.read_text())


def normalize_method_name(name: str) -> str:
    """
    Normalize a client method name or operationId for matching one to the other.

    The generator's snake_case names don't follow plain camelCase splitting (operationId variantsFromVariantID is
    variants_from_variant_id), so both sides drop underscores and case instead.

    Args:
        name: Client method name or operationId

    Returns:
        The name without underscores, in lower case
    """
    return name.replace('_', '').lower()


@cache
def operations() -> dict[str, tuple[str, dict[str, Any]]]:
    """
    Index the spec's operations by normalized operationId.

    Returns:
        Normalized operationId -> (path, operation)

    Raises:
        SpecError: If two operations normalize to the same name
    """
    index: dict[str, tuple[str, dict[str, Any]]] = {}
    for path, item in load_spec()['paths'].items():
        for http_method, op in item.items():
            if http_method not in HTTP_METHODS or 'operationId' not in op:
                continue
            key = normalize_method_name(op['operationId'])
            if key in index:
                raise SpecError(f'operationIds of {index[key][0]} and {path} both normalize to {key!r}')
            index[key] = (path, op)
    return index


def operation(client_method: str) -> tuple[str, dict[str, Any]]:
    """
    Find the spec operation of a generated client method.

    Args:
        client_method: AsyncIgvfCatalogApi method name (e.g., "genes_from_variants")

    Returns:
        (path, operation), the path without the server's /api prefix (e.g., "/variants/genes")

    Raises:
        SpecError: If the spec has no operation for the method
    """
    try:
        return operations()[normalize_method_name(client_method)]
    except KeyError:
        raise SpecError(f'The catalog OpenAPI spec has no operation for client method {client_method!r}') from None


def param_schema(client_method: str, name: str) -> dict[str, Any] | None:
    """
    Get the schema of a query parameter of a client method's operation.

    Args:
        client_method: AsyncIgvfCatalogApi method name
        name: Query parameter name

    Returns:
        The parameter's schema, or None if the operation has no such query parameter
    """
    _, op = operation(client_method)
    for param in op.get('parameters', []):
        if param.get('name') == name and param.get('in') == 'query':
            return param.get('schema', {})
    return None


def param_enum(client_method: str, name: str) -> list[str] | None:
    """
    Get the allowed values of a query parameter, in spec order.

    Args:
        client_method: AsyncIgvfCatalogApi method name
        name: Query parameter name

    Returns:
        The parameter's enum, or None if the parameter doesn't exist or takes any value
    """
    schema = param_schema(client_method, name)
    if schema is None or 'enum' not in schema:
        return None
    return list(schema['enum'])


def max_page_size(client_method: str) -> int | None:
    """
    Get the maximum page size (limit) of a client method's operation, as its description states it.

    Args:
        client_method: AsyncIgvfCatalogApi method name

    Returns:
        The maximum limit, or None if the description doesn't state one
    """
    _, op = operation(client_method)
    match = MAX_PAGE_SIZE.search(op.get('description') or '')
    return int(match.group(1)) if match else None
