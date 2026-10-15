"""Tests for the MCP server instance."""

from igvf_catalog_mcp import __version__
from igvf_catalog_mcp.server import app


def test_server_reports_package_version():
    options = app.create_initialization_options()

    assert options.server_name == 'igvf-catalog-mcp'
    assert options.server_version == __version__
