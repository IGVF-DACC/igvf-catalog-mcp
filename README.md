# IGVF Catalog MCP Server

An MCP (Model Context Protocol) server providing LLM-friendly access to the IGVF Catalog genomics knowledge graph.

## Features

- **Smart Entity Lookup**: Auto-detects entity type from ID patterns (genes, variants, proteins, etc.)
- **Genomic Region Search**: Flexible region format parsing with multi-entity queries
- **Relationship Discovery**: Find eQTLs, GWAS associations, protein interactions, and more
- **ID Translation**: Convert between variant ID formats (rsID, SPDI, HGVS, etc.)
- **Data Source Discovery**: Dynamically discover available datasets and filters

## Installation

The server is published on PyPI as [`igvf-catalog-mcp`](https://pypi.org/project/igvf-catalog-mcp/). Run it without installing anything using [uv](https://docs.astral.sh/uv/):

```bash
uvx igvf-catalog-mcp
```

or install it with pip and run the `igvf-catalog-mcp` command:

```bash
pip install igvf-catalog-mcp
igvf-catalog-mcp
```

To use it from an MCP client such as Claude Desktop or Claude Code, register it as a stdio server:

```json
{
  "mcpServers": {
    "igvf-catalog": {
      "command": "uvx",
      "args": ["igvf-catalog-mcp"]
    }
  }
}
```

## Usage

Configure the API URL (optional):

```bash
export IGVF_CATALOG_API_URL=https://api.catalogkg.igvf.org  # default
# or for development:
export IGVF_CATALOG_API_URL=https://catalog-api-dev.demo.igvf.org
export IGVF_CATALOG_API_URL=http://localhost:2023
```

`/api` is appended to the URL if it is not already there.

## Tools

### 1. `igvf_catalog_get_entity`
Look up any entity by ID with automatic type detection.

```json
{"id": "BRCA1"}
{"id": "rs12345"}
{"id": "ENSG00000141510"}
{"id": "lupus", "hint": "disease", "limit": 50, "page": 1}
```

### 2. `igvf_catalog_search_region`
Find all entities within a genomic region.

```json
{"region": "chr17:41000000-42000000"}
```

### 3. `igvf_catalog_find_associations`
Discover relationships between entities.

```json
{"entity_id": "TP53", "relationship": "regulatory"}
{"entity_id": "lupus", "relationship": "genetic", "hint": "disease"}
```

### 4. `igvf_catalog_find_ld`
Find variants in linkage disequilibrium with a query variant.

```json
{"variant_id": "rs429358", "ancestry": "EUR", "r2_threshold": 0.8}
```

### 5. `igvf_catalog_resolve_id`
Convert between identifier formats.

```json
{"id": "rs80357906"}
```

### 6. `igvf_catalog_list_sources`
Discover available data sources.

```json
{"category": "gene_expression"}
```

## Skills

Skills are pre-packaged Claude Code workflows that combine multiple tools into guided analyses. Invoke them directly with `/skill-name` in a Claude Code session (e.g., `/igvf-catalog-variant-report rs429358`). The agent can independently invoke the skills when they are relevant.

To enable skills, copy the desired skill directories from `skills/` into `~/.claude/skills/` (or wherever you store your Claude Code skills).

### `/igvf-catalog-variant-report`
Interpret a genetic variant's biological significance — disease associations, eQTLs, pharmacogenomics, coding impact, and linkage disequilibrium. Produces a structured summary of what a variant does and which conditions it's linked to.

### `/igvf-catalog-gene-dossier`
Build a comprehensive profile of a gene — disease links, regulatory elements, protein interactions, pathways, and transcript isoforms. Useful when you want a full picture of a gene's biology and clinical relevance.

### `/igvf-catalog-dissect-locus`
Identify the causal gene(s) at a GWAS locus by integrating LD proxies, eQTL evidence, and overlapping regulatory elements. Takes a GWAS lead variant and returns a ranked list of candidate genes with supporting evidence.

### `/igvf-catalog-regulatory-landscape`
Map how a gene is regulated — cis-regulatory elements, eQTL variants driving its expression, and tissue-specific patterns. Highlights which regulatory variants converge on disease associations.

### `/igvf-catalog-disease-genes`
Map the genetic architecture of a disease — causal genes, shared biological pathways, protein interaction networks, and potential therapeutic targets. Useful for understanding the gene network underlying a trait or condition.

### `/igvf-catalog-ld-compare`
Compare linkage disequilibrium structure for a variant across ancestries (EUR, AFR, EAS, SAS). Useful for assessing PRS portability, identifying ancestry-specific tag SNPs, and understanding population differences in LD.

## Development

Install from a clone with the development extras and run the linter and tests:

```bash
pip install -e ".[dev]"
ruff check
pytest
```

The tests run offline. `tests/test_contract.py` checks that every API method and parameter the server uses exists in the generated client, so it fails when the catalog API drops or renames something the server relies on.

## Architecture

The server consists of:
- **Tools**: 6 MCP tools for genomics queries
- **Services**: API client, edge endpoint registry, ID parser, region parser
- **Resources**: Entity schemas and examples

API calls go through [`igvf-catalog-async-client`](https://github.com/IGVF-DACC/igvf-catalog-async-python-client), the async Python client generated from the IGVF Catalog OpenAPI spec. `services/edge_config.py` maps each relationship to a generated client method.

## Versioning

The MCP server's version always equals the IGVF Catalog version it targets: `igvf-catalog-mcp` X.Y.Z depends on `igvf-catalog-async-client==X.Y.Z`. When the catalog is released, the release job pins the new client version, sets the same version in `src/igvf_catalog_mcp/__init__.py`, and publishes to PyPI.

Fixes to the MCP server between catalog releases are published by hand as `X.Y.Z.postN` (for example `1.3.0.post1`): set the version in `src/igvf_catalog_mcp/__init__.py`, then either publish a GitHub release or run the "Publish to PyPI" workflow with `workflow_dispatch`.

The `dev` branch tracks `igvf-catalog@dev`; its CI installs the async client from the client repo's `dev` branch.

## License

MIT
