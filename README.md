# IGVF Catalog MCP Server

An MCP (Model Context Protocol) server providing LLM-friendly access to the IGVF Catalog genomics knowledge graph.

## Features

- **Smart Entity Lookup**: Auto-detects entity type from ID patterns (genes, variants, proteins, etc.)
- **Genomic Region Search**: Flexible region format parsing with multi-entity queries
- **Relationship Discovery**: Find eQTLs, GWAS associations, protein interactions, and more
- **ID Translation**: Convert between variant ID formats (rsID, SPDI, HGVS, etc.)
- **Data Source Discovery**: Dynamically discover available datasets and filters

## Installation

```bash
cd igvf-catalog-mcp
pip install -e ".[dev]"
```

## Usage

Configure the API URL (optional):

```bash
export IGVF_CATALOG_API_URL=https://api.catalog.igvf.org  # default
# or for development:
export IGVF_CATALOG_API_URL=http://localhost:2023
```

Run the MCP server:

```bash
python -m igvf_catalog_mcp.server
```

## Tools

### 1. `igvf-catalog-get_entity`
Look up any entity by ID with automatic type detection.

```json
{"id": "BRCA1"}
{"id": "rs12345"}
{"id": "ENSG00000141510"}
```

### 2. `igvf-catalog-search_region`
Find all entities within a genomic region.

```json
{"region": "chr17:41000000-42000000"}
```

### 3. `igvf-catalog-find_associations`
Discover relationships between entities.

```json
{"entity_id": "TP53", "relationship": "regulatory"}
```

### 4. `igvf-catalog-find_ld`
Find variants in linkage disequilibrium with a query variant.

```json
{"variant_id": "rs429358", "ancestry": "EUR", "r2_threshold": 0.8}
```

### 5. `igvf-catalog-resolve_id`
Convert between identifier formats.

```json
{"id": "rs80357906"}
```

### 6. `igvf-catalog-list_sources`
Discover available data sources.

```json
{"category": "gene_expression"}
```

## Development

Run tests:

```bash
pytest
```

## Architecture

The server consists of:
- **Tools**: 6 MCP tools for genomics queries
- **Services**: API client, ID parser, region parser
- **Resources**: Entity schemas and examples

## License

MIT
