---
name: ld-compare
description: Compare LD structure across ancestries (EUR, AFR, EAS, SAS, AMR) for a variant. Use when someone asks about cross-population LD, PRS portability, ancestry-specific tag SNPs, or population differences in linkage disequilibrium.
argument-hint: <variant_id>
---

# Cross-Population LD Comparison

This skill queries the **IGVF Catalog MCP server** (`igvf-catalog`), which exposes a genomics knowledge graph through six tools: `igvf_catalog_get_entity`, `igvf_catalog_search_region`, `igvf_catalog_find_associations`, `igvf_catalog_find_ld`, `igvf_catalog_resolve_id`, and `igvf_catalog_list_sources`. The server must be configured and running.

Compare LD structure across all five superpopulations for variant `$ARGUMENTS`.

## Workflow

### Step 1: Resolve Variant
Call `igvf_catalog_resolve_id(id=$ARGUMENTS)` to normalize the identifier.

### Step 2: Query All Populations (parallel)
Run all five in parallel:

- `igvf_catalog_find_ld(variant_id, ancestry="EUR", r2_threshold=0.5, limit=100)`
- `igvf_catalog_find_ld(variant_id, ancestry="AFR", r2_threshold=0.5, limit=100)`
- `igvf_catalog_find_ld(variant_id, ancestry="EAS", r2_threshold=0.5, limit=100)`
- `igvf_catalog_find_ld(variant_id, ancestry="SAS", r2_threshold=0.5, limit=100)`
- `igvf_catalog_find_ld(variant_id, ancestry="AMR", r2_threshold=0.5, limit=100)`

### Step 3: Analyze

For each population: total partners at r2 > 0.5, count at r2 > 0.8, best proxy, LD block span.

Cross-reference:
- **Universal proxies:** r2 > 0.8 across all populations (ancient haplotypes, rare and valuable)
- **Population-specific proxies:** strong LD in one population, weak/absent in others
- **AFR pattern:** typically shorter LD blocks (older population, more recombination)

### Step 4: Compile Report

**Query Variant**
Identifier, coordinates, alleles.

**Population Summary**

| Population | r2>0.5 | r2>0.8 | Block span | Best proxy (r2) |
|-----------|--------|--------|------------|-----------------|

**Universal Proxies**
Variants in strong LD across all/most (4+) populations — reliable cross-ancestry tags.

**Population-Specific Proxies**
Variants in strong LD in 1-2 populations only. Show r2 across all ancestries.

**Cross-Population Matrix** (top variants)

| Variant | EUR | AFR | EAS | SAS | AMR |
|---------|-----|-----|-----|-----|-----|

**Interpretation**
3-5 sentences: block size comparison, AFR pattern, universal proxy availability, PRS portability implications, fine-mapping utility of AFR data.

## Interpretation Guide

- **AFR has shortest LD blocks** — older population, more recombination. EUR/EAS tend to have longer blocks.
- **European tag SNP may be uninformative in AFR** — major driver of poor PRS portability across ancestries
- **Shorter AFR blocks = fine-mapping advantage** — fewer candidate causal variants per locus
- **Universal proxies** indicate ancient haplotypes predating out-of-Africa migration
- **r2 thresholds:** >0.8 strong, 0.5-0.8 moderate, <0.3 weak
