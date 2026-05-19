# Changelog

## [Unreleased]

### Added
- **Pagination support for all multi-result tools**: `find_ld`, `find_associations`, and `search_region` now accept a `page` parameter (0-indexed) and return a `_pagination` metadata object in every response. The metadata includes `has_more`, `next_page`, and a natural-language `note` prompting agents to fetch subsequent pages when results are truncated.
- **`build_pagination_metadata` helper** in `formatter.py`: Shared utility that computes pagination signals using the heuristic "results_returned == limit implies more pages exist".

### Fixed
- **API client page override bug**: `IGVFCatalogClient.find_associations()` previously overwrote the `page` parameter to 0 regardless of what the tool passed. Now respects the page value from params.
- **ID Parser gene symbol parameter**: Changed gene symbol detection to return `"gene_name"` instead of `"name"` as the parameter name. This ensures compatibility with edge endpoints (e.g., `/api/genes/variants`, `/api/variants/genes`) which expect `gene_name`, while maintaining compatibility with node endpoints (e.g., `/api/genes`) which accept both `name` and `gene_name`. This fix resolves issues where `find_associations` tool would fail when querying relationships for gene symbols like "TP53" or "BRCA1".

### Changed
- **Tool descriptions** for `find_ld`, `find_associations`, and `search_region` now explicitly mention pagination support, making the capability visible to agents reading the tool schema.

## [0.1.0] - Initial Release

### Added
- Complete MCP server implementation with 5 tools
- Smart entity lookup with auto-detection for 30+ ID patterns
- Flexible genomic region parsing (supports M/K notation, commas, etc.)
- Async API client with httpx
- Comprehensive test suite
- MCP resources for schemas and guides
