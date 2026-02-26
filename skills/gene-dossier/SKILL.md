---
name: igvf-catalog-gene-dossier
description: Comprehensive gene profile — disease links, regulatory elements, interactions, pathways, and isoforms. Use when someone asks "tell me about gene X", "what do we know about BRCA1?", or wants a complete gene overview.
argument-hint: <gene>
---

# Comprehensive Gene Profile

This skill queries the **IGVF Catalog MCP server** (`igvf-catalog`), which exposes a genomics knowledge graph through six tools: `igvf_catalog_get_entity`, `igvf_catalog_search_region`, `igvf_catalog_find_associations`, `igvf_catalog_find_ld`, `igvf_catalog_resolve_id`, and `igvf_catalog_list_sources`. The server must be configured and running.

Build a 360-degree dossier for gene `$ARGUMENTS`.

## Workflow

### Step 1: Get Gene Identity
Call `igvf_catalog_get_entity(id=$ARGUMENTS)` to get coordinates, biotype, synonyms, HGNC/Entrez/Ensembl IDs.

### Step 2: Gather Associations (parallel)
Run these in parallel:

- `igvf_catalog_find_associations(entity_id, relationship="genetic")` — Disease associations (Orphanet association types, ClinGen)
- `igvf_catalog_find_associations(entity_id, relationship="regulatory")` — eQTL/sQTL variants across tissues
- `igvf_catalog_find_associations(entity_id, relationship="physical")` — Genetic interactions (BioGRID) + protein-protein interactions
- `igvf_catalog_find_associations(entity_id, relationship="functional")` — Reactome pathway memberships
- `igvf_catalog_find_associations(entity_id, relationship="transcription")` — GENCODE transcript isoforms

### Step 3: Regulatory Element Census
Call `igvf_catalog_search_region(region=<gene_coordinates>)` to find ENCODE SCREEN cis-regulatory elements overlapping the gene.

### Step 4: Compile Dossier

**Gene Summary**
Symbol, name, biotype, all IDs, genomic location (GRCh38).

**Disease Associations**
Grouped by type: Disease-causing > Susceptibility > Modifying > Biomarker > Candidate. Include disease name, ID, source.

**Regulatory Landscape**
Regulatory element counts by type (PLS, pELS, dELS, CTCF, CA, TF). Top eQTL variants. Tissues with strongest signal.

**Interaction Network**
Genetic interactions grouped by type. Highlight synthetic lethal partners (therapeutically relevant). PPI partners. Total count.

**Pathway Context**
Reactome pathways, grouped by top-level category if possible.

**Transcript Isoforms**
IDs with biotype. Protein-coding vs non-coding count.

**Summary**
2-4 sentences: primary biological role, strongest disease links, notable interactions, well-characterized vs understudied.

## Interpretation Guide

- **Orphanet types (ranked):** Disease-causing germline > somatic > Major susceptibility > Modifying > Candidate > Role in phenotype > Biomarker
- **Synthetic lethal interactions** identify drug targets: if gene A is mutated in cancer, inhibiting partner B may selectively kill cancer cells
- **Regulatory element types:** PLS (promoter, high H3K4me3), pELS (proximal enhancer <2kb TSS), dELS (distal enhancer >2kb), CTCF (insulator), CA (accessible, unclassified), TF (TF binding)
- **Many transcript isoforms** often indicates complex tissue-specific regulation
