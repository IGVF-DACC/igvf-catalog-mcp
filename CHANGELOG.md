# Changelog

## [Unreleased]

### Changed
- **API calls use the generated async client**: the hand-written httpx client is replaced by a thin wrapper (`services/api_client.py`) around `AsyncIgvfCatalogApi` from [`igvf-catalog-async-client`](https://github.com/IGVF-DACC/igvf-catalog-async-python-client). One client is shared by the server process and closed on shutdown. `IGVF_CATALOG_API_URL` still takes the host; `/api` is appended if missing.
- **`edge_config.py` names client methods**: each edge endpoint has a `client_method` (e.g. `genes_from_variants`) and a `path` without the `/api` prefix, so `_endpoint_path` and `list_sources` now show paths like `/variants/genes`. Verbose support is read from the generated method signature.
- **Gene symbols and pathways use the node endpoint parameter names**: `IDParser` returns `name` for gene symbols and `id` for Reactome pathways, which is what `/genes` and `/pathways` accept. `find_associations` maps them to the edge parameters (`gene_name`, …).
- **Versioning**: the version is read from `src/igvf_catalog_mcp/__init__.py` and follows the IGVF Catalog version (see README). Added the `igvf-catalog-mcp` console script, so the server runs with `uvx igvf-catalog-mcp`.
- **Dependencies**: removed `httpx` and `pydantic`; `mcp` is pinned below 2.0, whose server API this package does not support.

### Fixed
- **Endpoint parameters and filter values re-verified against the catalog OpenAPI spec**:
  - p-value filters send `neg_log10_pvalue` instead of `log10pvalue`. Previously the `p_value` filter was never applied.
  - GO term annotations query `/gene-products/go-terms` (the old `/annotations/go-terms` returned 404).
  - Gene symbol lookups in `get_entity` and `resolve_id` send `name`; previously the symbol was ignored and unrelated genes were returned. Pathway lookups send `id`.
  - Gene edges accept `synonym` instead of `alias`; protein edges accept `uniprot_name` and `uniprot_full_name` instead of `full_name`; ontology terms are sent as `disease_id` (not `disease_name`) to `/diseases/genes`.
  - Removed parameters the API does not have: `chr`/`position` (LD), `GENCODE_category` (variants/drugs), `disease_id`/`disease_name` (variants/diseases, now `assertion` and `pmid`), `files_fileset` (variants/coding-variants), `biosample_id`/`biosample_synonyms` (biosamples/genomic-elements), `biosample_*` (genomic-elements/genes, now `biosample_term`), and `log10pvalue` on variants/proteins and variants/genomic-elements.
  - Source, method and label values match the API enums (e.g. `EBI` instead of `EBI eQTL Catalogue`, `spliceQTL` instead of `splice_QTL`), and are only sent to endpoints that accept them. `AMR` was removed from the LD ancestries, which the API does not support.
  - Gene `regulatory` associations query `/genes/genomic-elements` for E2G predictions and CRISPR screens; `/genomic-elements/genes` only accepts a region, so this part of the query never returned results.
  - Identifier types an endpoint does not accept (e.g. an rsID for `/variants/coding-variants`) are reported in `query_metadata` without calling the API.
- Fixed existing `ruff check` errors.
- **`find_associations` returned only the first endpoint's rows**: every endpoint was queried with `limit`, but the combined list was then cut to `limit`, so later endpoints (e.g. `genes_genomic_elements` for a gene's `regulatory` relationship) were never visible on any page. `limit` now applies per endpoint and every fetched row is returned.

### Added
- **Contract tests** (`tests/test_contract.py`) checking every method and parameter used by the server against the generated client, and offline tests running all six tools through `call_tool`.
- **GitHub Actions**: `test.yml` (ruff and pytest on Python 3.10–3.13) and `release_to_pypi.yml` (trusted publishing to PyPI on GitHub releases).
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
