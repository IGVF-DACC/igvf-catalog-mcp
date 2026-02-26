"""Tests verifying all MCP tools have the igvf-catalog- prefix."""

from igvf_catalog_mcp.tools.get_entity import GET_ENTITY_TOOL
from igvf_catalog_mcp.tools.search_region import SEARCH_REGION_TOOL
from igvf_catalog_mcp.tools.find_associations import FIND_ASSOCIATIONS_TOOL
from igvf_catalog_mcp.tools.find_ld import FIND_LD_TOOL
from igvf_catalog_mcp.tools.resolve_id import RESOLVE_ID_TOOL
from igvf_catalog_mcp.tools.list_sources import LIST_SOURCES_TOOL

ALL_TOOLS = [
    GET_ENTITY_TOOL,
    SEARCH_REGION_TOOL,
    FIND_ASSOCIATIONS_TOOL,
    FIND_LD_TOOL,
    RESOLVE_ID_TOOL,
    LIST_SOURCES_TOOL,
]


def test_all_tool_names_have_prefix():
    for tool in ALL_TOOLS:
        assert tool.name.startswith('igvf_catalog_'), (
            f"Tool '{tool.name}' is missing the 'igvf_catalog_' prefix"
        )


def test_exact_tool_names():
    assert GET_ENTITY_TOOL.name == 'igvf_catalog_get_entity'
    assert SEARCH_REGION_TOOL.name == 'igvf_catalog_search_region'
    assert FIND_ASSOCIATIONS_TOOL.name == 'igvf_catalog_find_associations'
    assert FIND_LD_TOOL.name == 'igvf_catalog_find_ld'
    assert RESOLVE_ID_TOOL.name == 'igvf_catalog_resolve_id'
    assert LIST_SOURCES_TOOL.name == 'igvf_catalog_list_sources'
