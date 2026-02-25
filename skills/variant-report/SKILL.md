---
name: variant-report
description: Interpret a genetic variant — disease associations, eQTLs, pharmacogenomics, coding impact, and LD. Use when someone asks "what does this variant do?", "tell me about rs...", or wants to understand a variant's biological significance.
argument-hint: <variant_id>
---

# Variant Interpretation Report

This skill queries the **IGVF Catalog MCP server** (`igvf-catalog`), which exposes a genomics knowledge graph through six tools: `get_entity`, `search_region`, `find_associations`, `find_ld`, `resolve_id`, and `list_sources`. The server must be configured and running.

Generate a structured interpretation report for variant `$ARGUMENTS`.

## Workflow

### Step 1: Resolve Identity
Call `resolve_id(id=$ARGUMENTS)` to normalize identifiers (rsID, SPDI, HGVS, ClinGen). Note genomic coordinates for downstream queries.

### Step 2: Gather Evidence (parallel)
Run these in parallel:

- `find_associations(entity_id, relationship="genetic")` — GWAS phenotypes (OpenTargets), disease associations (ClinGen)
- `find_associations(entity_id, relationship="regulatory")` — eQTL/sQTL effects: genes, tissues, effect sizes
- `find_associations(entity_id, relationship="pharmacological")` — Drug interactions (PharmGKB): phenotype category, biogeographical group
- `find_associations(entity_id, relationship="coding")` — Protein impact predictions (dbNSFP): SIFT, PolyPhen, CADD, REVEL
- `find_ld(variant_id, ancestry="EUR", r2_threshold=0.8)` — LD proxy variants

### Step 3: Compile Report

**Variant Identity & Coordinates**
All identifiers, GRCh38 position, alleles.

**Disease & Phenotype Associations**
Ranked by p-value. Include trait, p-value, odds ratio/beta, source. Flag genome-wide significant (p < 5e-8).

**Regulatory Effects**
Grouped by target gene, then by tissue. Report effect direction. Highlight tissue-specific vs ubiquitous.

**Pharmacogenomics**
Grouped by drug. List phenotype category (Efficacy/Toxicity/Metabolism-PK/Dosage), biogeographical group, annotation level. Flag Level 1A/1B.

**Coding Impact** (if applicable)
Amino acid change, prediction scores with thresholds: SIFT (<0.05 = deleterious), PolyPhen (>0.85 = damaging), CADD (>20 = pathogenic), REVEL (>0.5 = pathogenic).

**LD Structure**
Proxy count at r2 > 0.8. Notable proxies with known annotations.

**Synthesis**
2-4 sentences: causal vs tag SNP? Regulatory vs coding mechanism? Which gene(s)? Clinical relevance?

## Interpretation Guide

- **p < 5e-8** = genome-wide significant; **p < 1e-5** = suggestive
- **GWAS hit + eQTL in disease-relevant tissue** = strong evidence for causal gene ("colocalization")
- **Many LD proxies** = large haplotype block, harder to fine-map; **few proxies** = variant itself may be causal
- **Most GWAS variants are non-coding** — strong eQTL + no coding impact → regulatory mechanism
- **PharmGKB levels:** 1A (guideline + strong evidence) > 1B > 2A > 2B > 3 > 4 (case report)
