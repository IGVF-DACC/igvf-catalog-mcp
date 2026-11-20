"""Tests for the MCP server instance."""

import json
import re

import pytest
from mcp.shared.exceptions import McpError
from mcp.shared.memory import create_connected_server_and_client_session
from pydantic import AnyUrl

from igvf_catalog_mcp import __version__
from igvf_catalog_mcp.resources.schemas import EXAMPLE_QUERIES_CONTENT
from igvf_catalog_mcp.server import app, list_tools


def test_server_reports_package_version():
    options = app.create_initialization_options()

    assert options.server_name == 'igvf-catalog-mcp'
    assert options.server_version == __version__


async def test_resources_list_and_read_through_the_sdk():
    """Resources are listed and readable over the MCP protocol, not just via the handlers.

    The SDK passes the URI to the read handler as a pydantic AnyUrl and expects
    ReadResourceContents back, which direct handler calls with strings don't exercise.
    """
    async with create_connected_server_and_client_session(app) as session:
        resources = (await session.list_resources()).resources
        assert {str(resource.uri) for resource in resources} == {
            'igvf://schemas/gene',
            'igvf://schemas/variant',
            'igvf://guide/identifiers',
            'igvf://examples/queries',
        }

        for resource in resources:
            result = await session.read_resource(resource.uri)
            assert len(result.contents) == 1
            content = result.contents[0]
            assert str(content.uri) == str(resource.uri)
            assert content.mimeType == resource.mimeType
            assert content.text.strip()
            if resource.mimeType == 'application/json':
                json.loads(content.text)


async def test_reading_an_unknown_resource_is_an_error():
    async with create_connected_server_and_client_session(app) as session:
        with pytest.raises(McpError, match='Unknown resource URI: igvf://nope'):
            await session.read_resource(AnyUrl('igvf://nope'))


async def test_example_queries_name_registered_tools():
    tool_names = {tool.name for tool in await list_tools()}
    example_tools = set(re.findall(r'^Tool: (\S+)$', EXAMPLE_QUERIES_CONTENT, re.MULTILINE))

    assert example_tools
    assert example_tools <= tool_names
