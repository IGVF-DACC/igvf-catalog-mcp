---
name: dissect-locus
description: Identify causal genes at a GWAS locus by integrating LD, eQTLs, and regulatory elements. Use when someone asks "which gene does this GWAS variant affect?", "fine-map this locus", or wants to go from GWAS signal to causal gene.
argument-hint: <variant_or_region>
---

# GWAS Locus Dissection

This skill queries the **IGVF Catalog MCP server** (`igvf-catalog`), which exposes a genomics knowledge graph through six tools: `get_entity`, `search_region`, `find_associations`, `find_ld`, `resolve_id`, and `list_sources`. The server must be configured and running.

Identify candidate causal genes at the locus defined by `$ARGUMENTS`.

## Workflow

### Step 1: Resolve Lead Variant
Call `resolve_id(id=$ARGUMENTS)` to get coordinates. If a region was provided, skip to Step 3.

### Step 2: Confirm GWAS Signal
Call `find_associations(entity_id, relationship="genetic")` to confirm phenotype(s), p-values, effect sizes.

### Step 3: Build Credible Set
Call `find_ld(variant_id, ancestry="EUR", r2_threshold=0.5)` — use moderate threshold to be inclusive. Note which variants have r2 > 0.8 (strong) vs 0.5-0.8 (moderate).

### Step 4: Survey the Locus
Define boundaries from the LD block (or lead +/- 500kb if few LD variants). Call `search_region(region, include=["genes", "regulatory_elements"])` to find all genes and regulatory elements.

### Step 5: eQTL Evidence
For the lead variant + up to 5 top LD variants (highest r2), call `find_associations(entity_id, relationship="regulatory")` in parallel. This reveals which genes' expression each variant affects and in which tissues.

### Step 6: Rank Genes

**Tier 1 — Strong:** Gene has eQTL variant in strong LD (r2 > 0.8) with lead GWAS variant, especially in disease-relevant tissue.

**Tier 2 — Moderate:** Gene has eQTL variant in moderate LD (0.5 < r2 < 0.8), or overlaps regulatory element harboring an LD variant.

**Tier 3 — Positional only:** Gene in the locus but no functional evidence linking it to the GWAS signal.

### Step 7: Compile Report

**Lead Variant & GWAS Signal**
Identifier, coordinates, trait(s), p-value(s), effect size(s).

**LD Block & Credible Set**
Total variants at r2 > 0.5 and > 0.8. Block span in kb.

**Candidate Causal Gene Ranking**

| Gene | Tier | eQTL evidence | LD support (r2) | Tissues | Distance to lead |
|------|------|---------------|-----------------|---------|-----------------|

For Tier 1-2: which variant(s) are eQTLs, their r2 with lead, effect direction/size, tissues.

**Regulatory Element Map**
Elements in the locus from ENCODE SCREEN. Which overlap LD variants.

**Interpretation**
3-5 sentences: strongest candidate(s) and why, nearest gene vs best candidate, likely mechanism, caveats.

## Interpretation Guide

- **Nearest gene is causal only ~50% of the time** — always prioritize functional evidence over proximity
- **Tissue context matters:** eQTL in disease-relevant tissue (pancreatic islets for T2D, liver for lipids) >> unrelated tissue
- **Multiple genes is common** — report all candidates rather than forcing a single answer
- **Regulatory convergence:** GWAS hit + eQTL + enhancer element = very strong regulatory mechanism evidence
- **Large LD blocks** (>500kb) make fine-mapping harder; African-ancestry data can help narrow candidates
