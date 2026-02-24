# IGVF Catalog Evaluation Framework

This directory contains the evaluation framework for comparing the IGVF Catalog MCP server against the llm-query RAG endpoint.

## Prerequisites

1. **For LLM-Query Evaluator**: Set the password environment variable:
   ```bash
   export IGVF_LLM_QUERY_PASSWORD="your-password-here"
   ```

2. **Questions**: Ensure `../EVALUATION.md` contains the questions to evaluate.

## How to Run the Evaluation

### Step 1: Run the MCP Evaluator

In Cursor, invoke the agent:
```
@igvf-mcp-evaluator
```

This will:
- Read questions from `EVALUATION.md`
- Use IGVF Catalog MCP tools to answer each question
- Write answers to `mcp_answers.md`

### Step 2: Run the LLM-Query Evaluator

In Cursor, invoke the agent:
```
@igvf-llmquery-evaluator
```

This will:
- Read questions from `EVALUATION.md`
- Call the llm-query API for each question
- Write answers to `llm_query_answers.md`

### Step 3: Compose the Comparison

In Cursor, invoke the agent:
```
@igvf-evaluation-composer
```

This will:
- Read both answer files
- Create a side-by-side comparison in `comparison.md`

## Output Files

| File | Description |
|------|-------------|
| `mcp_answers.md` | Answers from the MCP evaluator |
| `llm_query_answers.md` | Answers from the llm-query evaluator |
| `comparison.md` | Side-by-side comparison for human review |

## Helper Script

`llm_query_client.py` - A standalone script to query the llm-query endpoint:

```bash
# Basic usage
python llm_query_client.py "What is gene TP53?"

# With verbose output
python llm_query_client.py "What is gene TP53?" --verbose
```

## Modifying Questions

To change the evaluation questions, edit `../EVALUATION.md`. Each line should contain one question.
