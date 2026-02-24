# IGVF Catalog Evaluation Framework - Implementation Guide

> **Purpose**: This document provides context for LLM agents continuing development or maintenance of this evaluation framework.

## Overview

This evaluation framework compares two methods of answering genomics questions against the IGVF Catalog:

1. **MCP Method**: An LLM using the IGVF Catalog MCP server tools
2. **LLM-Query Method**: The IGVF Catalog's built-in RAG endpoint (`/api/llm-query`)

The goal is to help humans evaluate which approach provides better answers for different types of genomics queries.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Cursor IDE                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────┐    ┌──────────────────────┐                   │
│  │ @igvf-mcp-evaluator  │    │ @igvf-llmquery-      │                   │
│  │                      │    │  evaluator           │                   │
│  │ Uses MCP tools:      │    │                      │                   │
│  │ - get_entity         │    │ Uses:                │                   │
│  │ - search_region      │    │ - llm_query_client.py│                   │
│  │ - find_associations  │    │ - or curl            │                   │
│  │ - find_ld            │    │                      │                   │
│  │ - resolve_id         │    │                      │                   │
│  │ - list_sources       │    │                      │                   │
│  └──────────┬───────────┘    └──────────┬───────────┘                   │
│             │                           │                                │
│             ▼                           ▼                                │
│     mcp_answers.md              llm_query_answers.md                    │
│             │                           │                                │
│             └───────────┬───────────────┘                                │
│                         ▼                                                │
│           ┌─────────────────────────┐                                   │
│           │ @igvf-evaluation-       │                                   │
│           │  composer               │                                   │
│           └───────────┬─────────────┘                                   │
│                       ▼                                                  │
│               comparison.md                                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                    │                               │
                    ▼                               ▼
        ┌───────────────────┐           ┌───────────────────┐
        │ IGVF Catalog MCP  │           │ IGVF Catalog API  │
        │ Server (local)    │           │ /api/llm-query    │
        └─────────┬─────────┘           └───────────────────┘
                  │
                  ▼
        ┌───────────────────┐
        │ IGVF Catalog API  │
        │ REST endpoints    │
        └───────────────────┘
```

## File Structure

```
igvf-catalog/
├── .cursor/
│   └── agents/
│       ├── igvf-mcp-evaluator.md       # Agent: answers using MCP tools only
│       ├── igvf-llmquery-evaluator.md  # Agent: answers using llm-query API
│       └── igvf-evaluation-composer.md # Agent: creates comparison document
│
└── igvf-catalog-mcp/
    ├── EVALUATION.md                   # Questions to evaluate (input)
    │
    └── evaluation/
        ├── README.md                   # User-facing instructions
        ├── IMPLEMENTATION_GUIDE.md     # This file (LLM handoff)
        ├── llm_query_client.py         # Helper script for API calls
        │
        │   # Generated output files:
        ├── mcp_answers.md              # Output from MCP evaluator
        ├── llm_query_answers.md        # Output from llm-query evaluator
        └── comparison.md               # Final side-by-side comparison
```

## Component Details

### 1. Cursor Agents

Located in `.cursor/agents/`. These are Cursor-specific agent definition files.

#### `igvf-mcp-evaluator.md`
- **Purpose**: Answer evaluation questions using only IGVF Catalog MCP tools
- **Key constraint**: Must NOT use internet, training knowledge, or any other tools
- **Input**: Reads questions from `../EVALUATION.md`
- **Output**: Writes to `mcp_answers.md`
- **MCP tools available**:
  - `igvf-catalog-get_entity` - Entity lookup with auto-detection
  - `igvf-catalog-search_region` - Genomic region queries
  - `igvf-catalog-find_associations` - Relationship queries (eQTL, GWAS, etc.)
  - `igvf-catalog-find_ld` - Linkage disequilibrium queries
  - `igvf-catalog-resolve_id` - ID format conversion
  - `igvf-catalog-list_sources` - Data source discovery

#### `igvf-llmquery-evaluator.md`
- **Purpose**: Answer evaluation questions using the llm-query RAG endpoint
- **Key constraint**: Must use the API as-is, no interpretation of answers
- **Input**: Reads questions from `../EVALUATION.md`
- **Output**: Writes to `llm_query_answers.md`
- **Requires**: `IGVF_LLM_QUERY_PASSWORD` environment variable

#### `igvf-evaluation-composer.md`
- **Purpose**: Create human-readable comparison of both answer sets
- **Key constraint**: Must NOT judge correctness, only present side-by-side
- **Input**: Reads `mcp_answers.md` and `llm_query_answers.md`
- **Output**: Writes to `comparison.md`

### 2. Helper Script

#### `llm_query_client.py`
- **Purpose**: Simple Python client for the llm-query API
- **Dependencies**: None (uses only Python standard library)
- **Timeout**: 120 seconds (RAG queries can be slow)
- **Environment variables**:
  - `IGVF_LLM_QUERY_PASSWORD` (required)
  - `IGVF_CATALOG_API_URL` (optional, default: `https://api.catalogkg.igvf.org`)

**Usage**:
```bash
python llm_query_client.py "Your question here"
python llm_query_client.py "Your question here" --verbose
```

**Output**: JSON with `success`, `answer`, and optionally `error` fields.

### 3. Question File

#### `EVALUATION.md` (in parent directory)
- One question per line
- Plain text format
- Currently contains 14 genomics questions covering:
  - Entity lookups (genes, variants, proteins)
  - Region searches
  - Association queries (eQTL, disease, phenotype)
  - ID resolution
  - Filtering and sorting

## Workflow

### Standard Evaluation Run

1. **Prepare**: Ensure `IGVF_LLM_QUERY_PASSWORD` is set
2. **Run MCP Evaluator**: Invoke `@igvf-mcp-evaluator` in Cursor
3. **Run LLM-Query Evaluator**: Invoke `@igvf-llmquery-evaluator` in Cursor
4. **Compose Results**: Invoke `@igvf-evaluation-composer` in Cursor
5. **Human Review**: Open `comparison.md` and assess answer quality

### Re-running with New Questions

1. Edit `igvf-catalog-mcp/EVALUATION.md` with new questions
2. Delete or archive existing answer files
3. Run the three agents in order

## Key Design Decisions

### Why Cursor Agents?
- Native integration with the development environment
- Access to MCP tools without additional configuration
- Human can observe and intervene if needed
- No need for separate API keys (uses Cursor's Claude integration)

### Why Separate Agents Instead of One?
- **Isolation**: MCP agent must be strictly limited to MCP tools
- **Modularity**: Can re-run one evaluator without the other
- **Debugging**: Easier to identify which method failed
- **Flexibility**: Could add more evaluation methods later

### Why Not Automated Correctness Scoring?
- Genomics answers are complex and context-dependent
- "Correct" may mean different things (complete, accurate, relevant)
- Human judgment is more reliable for this domain
- Framework focuses on making comparison easy, not automated

### Why Plain Python for llm_query_client.py?
- No external dependencies = no installation issues
- Simple enough that it doesn't need httpx/requests
- Easy to understand and modify
- Works in any Python 3.x environment

## Output Format Specifications

### mcp_answers.md / llm_query_answers.md

```markdown
# [Evaluator Name] Answers

*Generated: [ISO timestamp]*

## Question 1
**Q:** [exact question text from EVALUATION.md]

**A:** [answer text]

---

## Question 2
...
```

### comparison.md

```markdown
# IGVF Catalog Evaluation: MCP vs LLM-Query Comparison

*Generated: [ISO timestamp]*

## Summary
- **Total Questions:** [N]
- **MCP Evaluator:** Completed [X] / [N]
- **LLM-Query Evaluator:** Completed [Y] / [N]

---

## Question 1: [brief summary]

**Full Question:** [text]

### MCP Answer
[answer]

### LLM-Query Answer
[answer]

---

## Observations
[Notable differences, patterns, failures]
```

## Potential Improvements

### Not Yet Implemented

1. **Automated metrics**: Response time, token count, API call count
2. **Batch mode**: Run all questions in parallel
3. **Retry logic**: Automatically retry failed questions
4. **Answer caching**: Skip questions that already have answers
5. **Diff highlighting**: Highlight differences between answers
6. **Confidence scoring**: Have each method rate its confidence

### Known Limitations

1. **Sequential execution**: Agents run one at a time
2. **No persistence**: Re-running overwrites previous answers
3. **Manual invocation**: User must invoke each agent separately
4. **Password handling**: llm-query password must be set manually

## Troubleshooting

### MCP Evaluator Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| "Unable to answer" for all questions | MCP server not connected | Check Cursor MCP configuration |
| Empty or partial results | API timeout | Increase timeout, retry |
| Wrong entity type detected | Ambiguous ID | Use more specific IDs in questions |

### LLM-Query Evaluator Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| "Password not set" error | Missing env var | `export IGVF_LLM_QUERY_PASSWORD=...` |
| HTTP 401/403 errors | Wrong password | Verify password is correct |
| Timeout errors | Slow RAG processing | Increase timeout in script (default: 120s) |
| Connection refused | Wrong API URL | Check `IGVF_CATALOG_API_URL` |

### Composer Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| "File not found" | Evaluators not run | Run both evaluators first |
| Mismatched questions | Different EVALUATION.md | Re-run both evaluators |
| Parsing errors | Malformed answer files | Check answer file format |

## Related Files

### In Parent MCP Server (`igvf-catalog-mcp/`)

- `IMPLEMENTATION_GUIDE.md` - Details on the MCP server implementation
- `README.md` - MCP server overview
- `src/igvf_catalog_mcp/tools/` - MCP tool implementations

### In Main Repo

- `src/routers/datatypeRouters/nodes/llm_query.ts` - llm-query endpoint implementation
- `docs/` - API documentation

## Contact & Resources

- **IGVF Catalog API**: https://api.catalogkg.igvf.org
- **MCP Protocol**: https://modelcontextprotocol.io/
- **Cursor Agents**: https://docs.cursor.com/context/agents

---

*Last updated: January 13, 2026*
*Created for evaluation framework comparing MCP tools vs llm-query RAG endpoint*
