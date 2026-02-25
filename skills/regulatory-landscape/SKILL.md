---
name: regulatory-landscape
description: Map how a gene is regulated — cis-regulatory elements, eQTL variants, tissue-specific patterns, and regulatory-disease convergence. Use when someone asks "how is this gene regulated?", "what controls expression of X?", or wants tissue-specific regulatory analysis.
argument-hint: <gene> [tissue]
---

# Regulatory Architecture Analysis

This skill queries the **IGVF Catalog MCP server** (`igvf-catalog`), which exposes a genomics knowledge graph through six tools: `get_entity`, `search_region`, `find_associations`, `find_ld`, `resolve_id`, and `list_sources`. The server must be configured and running.

Map the regulatory landscape of `$ARGUMENTS`.

Parse the arguments: the first token is the gene, and any subsequent token is an optional tissue/cell type filter.

## Workflow

### Step 1: Get Gene Coordinates
Call `get_entity(id=<gene>)` to get chr, start, end.

### Step 2: Survey Regulatory Elements
Extend gene coordinates by 500kb on each side. Call `search_region(region=<extended_coords>, include=["regulatory_elements"])` to find ENCODE SCREEN elements.

Classify by `source_annotation`: PLS (promoter), pELS (proximal enhancer <2kb TSS), dELS (distal enhancer >2kb), CTCF (insulator), CA (accessible, unclassified), TF (TF binding).

### Step 3: Gather eQTL/sQTL Data
Call `find_associations(entity_id=<gene>, relationship="regulatory", limit=100)`. If tissue specified, add `filters={biological_context: <tissue>}`.

### Step 4: Tissue-Specificity Analysis
Group eQTLs by `biological_context`:
- Count per tissue, rank by significance
- Identify tissue-specific vs ubiquitous variants
- If tissue specified, compare its profile to others

### Step 5: Regulatory-Disease Convergence
For the top 5-10 most significant eQTL variants, call `find_associations(entity_id=<variant>, relationship="genetic")` in parallel to check for GWAS overlaps.

### Step 6: Compile Report

**Gene Overview**
Symbol, coordinates, biotype. Regulatory window analyzed.

**Cis-Regulatory Element Census**
Total elements. Breakdown: PLS, pELS, dELS, CTCF, CA, TF. Notable patterns (e.g., enhancer clusters).

**eQTL/sQTL Landscape**
Total regulatory variants. Top variants: ID, p-value, beta, tissue, eQTL vs sQTL.

**Tissue-Specificity Profile**
Tissues ranked by eQTL count. Tissue-specific variants highlighted.

**Regulatory-Disease Convergence**
eQTL variants that are also GWAS hits: expression effect + disease/trait + GWAS p-value. This is the strongest evidence for regulatory disease mechanism.

**Interpretation**
3-5 sentences: regulatory complexity, key tissues, disease-relevant regulatory variants, overall architecture.

## Interpretation Guide

- **Many dELS elements** → complex enhancer-driven regulation; **mostly PLS** → simpler promoter-driven
- **Ubiquitous eQTLs** = constitutive regulation; **tissue-specific eQTLs** = more biologically interesting and disease-relevant
- **eQTL + GWAS convergence** = strong evidence that variant regulates gene X → gene X is causal for disease → tissue Y is disease-relevant
- **sQTLs** affect splicing (isoform ratios) — can be disease-relevant even when total expression is unchanged
- **dELS >100kb away** may still regulate the gene through chromatin looping
