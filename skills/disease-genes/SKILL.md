---
name: disease-genes
description: Map the genetic architecture of a disease — causal genes, shared pathways, interaction networks, and therapeutic targets. Use when someone asks "what genes cause X?", "genetic basis of...", or wants to understand the gene network underlying a disease.
argument-hint: <disease_name_or_id>
---

# Disease Gene Network

This skill queries the **IGVF Catalog MCP server** (`igvf-catalog`), which exposes a genomics knowledge graph through six tools: `igvf_catalog_get_entity`, `igvf_catalog_search_region`, `igvf_catalog_find_associations`, `igvf_catalog_find_ld`, `igvf_catalog_resolve_id`, and `igvf_catalog_list_sources`. The server must be configured and running.

Map the genetic architecture and gene network for `$ARGUMENTS`.

## Workflow

### Step 1: Find Disease and Genes

**If disease ID provided** (e.g., Orphanet_586, MONDO_0008199):
- `igvf_catalog_get_entity(id=<disease_id>)` for disease details
- `igvf_catalog_find_associations(entity_id=<disease_id>, relationship="genetic")` for associated genes

**If disease name provided** (e.g., "cystic fibrosis"):
- `igvf_catalog_get_entity(id=<disease_name>)` — may resolve to an ID
- If limited results, try the known primary gene (e.g., CFTR for cystic fibrosis) via `igvf_catalog_find_associations(entity_id=<gene>, relationship="genetic")` to find the disease ID, then query from disease side.

**Fallback:** The gene→disease direction is more reliable than disease→gene. If needed, query known genes with `igvf_catalog_find_associations(gene, relationship="genetic")` to confirm and discover associations.

### Step 2: Pathway Analysis (parallel)
For each disease gene (up to 10): `igvf_catalog_find_associations(entity_id=<gene>, relationship="functional")` → Reactome pathways.

### Step 3: Interaction Analysis (parallel)
For each disease gene (up to 10): `igvf_catalog_find_associations(entity_id=<gene>, relationship="physical")` → BioGRID genetic + protein-protein interactions.

### Step 4: Convergence Analysis

**Pathway convergence:** Pathways containing 2+ disease genes = core disrupted biology.

**Interaction hubs:** Non-disease genes interacting with 2+ disease genes = potential novel targets.

**Direct interactions:** Disease genes that interact with each other = same complex/pathway.

### Step 5: Compile Report

**Disease Overview**
Name, IDs (Orphanet, MONDO), gene count.

**Disease Gene Table**

| Gene | Association Type | Source | Notes |
|------|-----------------|--------|-------|

Ranked: Disease-causing > Susceptibility > Modifying > Biomarker > Candidate.

**Pathway Convergence**

| Pathway | Disease Genes | Total Genes |
|---------|--------------|-------------|

Pathways shared by 2+ disease genes, ranked.

**Interaction Network**
Direct disease gene interactions. Hub genes (non-disease genes interacting with 2+ disease genes).

| Hub Gene | Interacts With | Types |
|----------|---------------|-------|

**Therapeutic Insights**
Synthetic lethal partners, druggable hubs, pathway-based opportunities.

**Summary**
3-5 sentences: core biology, pathway clustering vs spread, hub gene targets, genetic architecture (monogenic/oligogenic/polygenic).

## Interpretation Guide

- **Orphanet types:** Disease-causing germline > somatic > Major susceptibility > Modifying > Candidate > Biomarker
- **Pathway convergence** is more informative than any single gene's pathways — shared pathways = disease mechanism
- **Hub genes** interacting with multiple disease genes are strong candidates for novel disease genes or therapeutic targets
- **Monogenic** (1-3 strong causal genes, e.g., CF/CFTR) vs **polygenic** (many susceptibility genes, e.g., T2D) — network structure reflects this
- **Synthetic lethality** (cancer): if gene A is mutated, inhibiting synthetic lethal partner B selectively kills tumor cells (basis of PARP inhibitors in BRCA cancers)
