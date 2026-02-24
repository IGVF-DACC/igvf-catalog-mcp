# IGVF Catalog Evaluation: MCP vs LLM-Query Comparison

*Generated: Tuesday Jan 13, 2026*

## Summary

- **Total Questions:** 14
- **MCP Evaluator:** Completed 14 / 14
- **LLM-Query Evaluator:** Completed 13 / 14 (1 error)

---

## Question 1: Gene TP53 Information

**Full Question:** Find information about gene TP53.

### MCP Answer
TP53 (ENSG00000141510) is a protein-coding gene located on chromosome 17 (chr17:7661778-7687538) on the minus strand. It is also known as "tumor protein p53" or "tumor supressor p53". TP53 is part of the Morphic and ACMG73 collections. Other synonyms include: BCC7, P53, LFS1, TRP53, BMFS5, antigen NY-CO-13. The gene is sourced from GENCODE v43.

### LLM-Query Answer
TP53 is a protein-coding gene located on chromosome 17 (chr17), spanning positions 7,661,778 to 7,687,538 on the negative strand. It is also known by several synonyms, including P53, tumor suppressor p53, cellular tumor antigen p53, and LFS1, among others. TP53 is associated with study sets such as MorPhiC and IGVFFI6537JARB, and is included in collections like MorphiC and ACMG73. The gene is cataloged in the GENCODE v43 release, with the HGNC identifier HGNC:11998 and Entrez Gene ID 7157. TP53 plays a crucial role in regulating cell division and preventing tumor formation, making it a key gene in cancer research.

---

## Question 2: Variants at chr16:20000000

**Full Question:** Show all the variants in chromosome 16, position at 20000000?

### MCP Answer
Found 12 variants in the region chr16:19999990-20000010:
1. NC_000016.10:19999991:T:C (rs1228245973) - bravo_af: 3.778e-06
2. NC_000016.10:19999992:A:G (rs2057194804)
3. NC_000016.10:19999995:T:G (rs1471226543)
4. NC_000016.10:19999996:G:A (rs1159183926)
5. NC_000016.10:19999996:G:C (rs1159183926)
6. NC_000016.10:20000001:A:C (rs1300186376)
7. NC_000016.10:20000001:A:G (rs1300186376)
8. NC_000016.10:20000003:A:G (rs927780620)
9. NC_000016.10:20000006:G:C (rs2057194837)
10. NC_000016.10:20000009:C:A (rs576444245)
11. NC_000016.10:20000009:C:G (rs576444245)
12. NC_000016.10:20000010:TTTTT:TTTT (rs2057194846)

### LLM-Query Answer
There are no variants found in chromosome 16 at position 20,000,000.

---

## Question 3: Diseases for Variant NC_000012.12:102917129:T:C

**Full Question:** What diseases the variant with SPDI NC_000012.12:102917129:T:C is associated with?

### MCP Answer
The variant NC_000012.12:102917129:T:C is associated with **MONDO_0009861** (Phenylketonuria) through the **PAH** gene (ENSG00000171759). The association is classified as **Pathogenic** and is supported by PubMed references: 2574002 and 9450897.

### LLM-Query Answer
The variant with SPDI NC_000012.12:102917129:T:C is associated with phenylketonuria. Phenylketonuria (PKU) is the most common inborn error of amino acid metabolism and is characterized by mild to severe mental disability in untreated patients. This disease is also known by several other names, including PKU, phenylpyruvic oligophrenia, and phenylalanine hydroxylase deficiency.

---

## Question 4: Lupus-Related Variants

**Full Question:** Find variants that are relevant to lupus disease.

### MCP Answer
Unable to answer with available MCP tools. While I found the lupus disease entry (MONDO_0007915 - "systemic lupus erythematosus" and Orphanet_536), querying for variant associations with these disease IDs returned no results. The IGVF Catalog MCP tools do not currently have direct disease-to-variant associations indexed for lupus.

### LLM-Query Answer
No variants relevant to lupus disease were found in the database.

---

## Question 5: CTCF Protein Transcripts

**Full Question:** Find transcripts from human protein CTCF?

### MCP Answer
The human CTCF protein (ENSP00000264010, UniProt P49711) is translated from transcript **ENST00000264010**. The protein is named "Transcriptional repressor CTCF" and the source is GENCODE.

### LLM-Query Answer
Here are five human transcripts associated with the protein CTCF:
- CTCF-215 (ENST00000646076.1)
- CTCF-201 (ENST00000264010.10)
- CTCF-202 (ENST00000401394.6)
- CTCF-209 (ENST00000644753.1)
- CTCF-205 (ENST00000642819.1)

Each transcript is annotated in the GENCODE v43 release and spans a region on the positive strand of chromosome 16.

---

## Question 6: Genomic Elements for rs62513865

**Full Question:** Tell me about genetic elements overlapping with variant rs62513865?

### MCP Answer
The variant rs62513865 (NC_000008.11:100579984:C:T) is located on chr8 at position 100,579,984 (ref: C, alt: T). It has a gnomAD total allele frequency of 0.047 and is classified as "noncoding" by GENCODE. Searching for regulatory associations and genomic elements overlapping this variant returned **no results**.

### LLM-Query Answer
*Error: An unexpected error occurred. (INTERNAL_SERVER_ERROR)*

---

## Question 7: Liver Tissue eQTL Variants

**Full Question:** What variants are active in liver tissue, consider eQTL data specifically.

### MCP Answer
Unable to answer with available MCP tools. The MCP tools do not support a direct query for all eQTL variants filtered by a specific tissue type (liver).

### LLM-Query Answer
No variants were identified as being active in liver tissue based on the available eQTL data. This means that, according to the current database, there are no documented variant-gene associations specifically linked to liver tissue through eQTL evidence.

---

## Question 8: BRCA1 Genomic Elements (score > 0.70)

**Full Question:** Find the genomic elements that are associated with BRCA1 where score is larger than 0.70.

### MCP Answer
Unable to answer with available MCP tools. While I found many gene-variant associations (eQTLs, splice_QTLs) for BRCA1 (ENSG00000012048), the genomic_elements_genes endpoint returned a 404 error.

### LLM-Query Answer
The following genomic elements are strongly associated with the BRCA1 gene (with a score greater than 0.70). All identified elements are promoter regions located on chromosome 17, near the BRCA1 locus. These promoters were predicted using the ENCODE-rE2G method for regulatory interaction and are classified as accessible DNA elements. The elements are supported by data from various biological samples, including neural crest cells, T-cells, right lung, and head of caudate nucleus.

---

## Question 9: eQTLs in Orphanet_101435

**Full Question:** Find the top 5 (sorted by p_value in ascending order) eQTLs in ontology term Orphanet_101435.

### MCP Answer
Unable to answer with available MCP tools. Searching for regulatory associations with ontology term Orphanet_101435 returned the error "Relationship type 'regulatory' not applicable to ontology entities."

### LLM-Query Answer
No eQTLs were found that are associated with the ontology term "Orphanet_101435." As a result, there are no top eQTLs to report for this term.

---

## Question 10: Genomic Elements Containing rs6994300

**Full Question:** Find the genomic elements that it is containing variant rs6994300.

### MCP Answer
The variant rs6994300 (NC_000008.11:101557588:G:A) is located at chr8:101,557,588. Searching the region found one overlapping regulatory element:
- **EH38E3848787**: A candidate cis regulatory element (dELS: distal Enhancer-like signal) spanning chr8:101557365-101557713, sourced from ENCODE (ENCFF420VPZ).

### LLM-Query Answer
The variant rs6994300 is located within a genomic element named EH38E3848787 on chromosome 8, spanning positions 101,557,365 to 101,557,713. This element is classified as a candidate cis-regulatory element with a distal enhancer-like signal annotation, identified by the ENCODE project. More information: https://www.encodeproject.org/files/ENCFF420VPZ.

---

## Question 11: Genes Co-expressed with ENSG00000012048

**Full Question:** Find the top 5 genes (sorted by z_score in ascending order) that are co-expressed with gene ENSG00000012048.

### MCP Answer
Unable to answer with available MCP tools. The genes_genes endpoint returned associations for ENSG00000012048 (BRCA1), but the tool does not provide z_score values or direct coexpression metrics.

### LLM-Query Answer
Top 5 genes co-expressed with ENSG00000012048, sorted by z_score:
1. **ENSG00000114125**: z_score -3.76 (CoXPresdb, GO:0010467)
2. **ENSG00000122203**: z_score -3.37 (CoXPresdb, GO:0010467)
3. **ENSG00000168890**: z_score -3.1 (CoXPresdb, GO:0010467)
4. **ENSG00000092201**: z_score 0 (BioGRID, synthetic growth defect)
5. **ENSG00000118260**: z_score 0 (BioGRID, phenotypic enhancement)

---

## Question 12: Genes Linked to NC_000020.11:3658947:A:G

**Full Question:** Which genes are linked to variant with SPDI NC_000020.11:3658947:A:G?

### MCP Answer
The variant NC_000020.11:3658947:A:G (rs6139176) is located on chr20 at position 3,658,947. Querying for gene associations returned **no results**.

### LLM-Query Answer
No genes are currently linked to the variant with SPDI NC_000020.11:3658947:A:G in the database.

---

## Question 13: Is rs6994300 an eQTL?

**Full Question:** Is variant rs6994300 an eQTL?

### MCP Answer
Based on the available MCP tools, **no eQTL associations were found** for variant rs6994300 (NC_000008.11:101557588:G:A). However, the variant does overlap with an enhancer-like element (EH38E3848787), suggesting potential regulatory function.

### LLM-Query Answer
Based on the available data, there is no evidence that the variant rs6994300 is classified as an eQTL in the database.

---

## Question 14: Variants Associated with BRCA1

**Full Question:** Find 5 variants associated to gene BRCA1.

### MCP Answer
5 eQTL variants associated with BRCA1:
1. **NC_000017.11:43342666:A:G** - eQTL, log10pvalue: 9.90
2. **NC_000017.11:43323833:G:T** - eQTL, log10pvalue: 9.90
3. **NC_000017.11:43325505:T:C** - eQTL, log10pvalue: 9.90
4. **NC_000017.11:43306755:A:G** - eQTL, log10pvalue: 9.95
5. **NC_000017.11:43127543:G:C** - eQTL, log10pvalue: 10.01, effect_size: 0.151

### LLM-Query Answer
5 variants associated with BRCA1 (clinical significance):
1. **NC_000017.11:43041892:A:T** (rs8071278) - Benign, familial breast-ovarian cancer
2. **NC_000017.11:43050670:G:A** (rs8070179) - Benign, familial breast-ovarian cancer
3. **NC_000017.11:43077839:G:A** (rs4239148) - Benign, familial breast-ovarian cancer
4. **NC_000017.11:43092918:G:A** (rs799917) - Benign, hereditary breast and ovarian cancer
5. **NC_000017.11:43119276:AAAAAAAAAAAA:AAAAAAAAAAA** (rs61461583) - Benign, deletion variant

---

## Observations

### Notable Differences

1. **Question 2 (Variants at chr16:20000000)**: The MCP evaluator found 12 variants by searching a small region around the position, while the LLM-Query returned no results. This suggests different interpretation of the query - MCP used a region search while LLM-Query may have searched for an exact position match.

2. **Question 5 (CTCF Transcripts)**: The LLM-Query provided 5 transcripts while MCP found only 1. LLM-Query appears to have access to more comprehensive transcript data or used a different query approach.

3. **Question 8 (BRCA1 Genomic Elements)**: LLM-Query successfully retrieved genomic elements with score filtering, while MCP encountered a 404 error on the genomic_elements_genes endpoint.

4. **Question 11 (Gene Coexpression)**: LLM-Query successfully retrieved z_score values for coexpression, while MCP could not access this data through its tools.

5. **Question 14 (BRCA1 Variants)**: Both found variants but from different perspectives - MCP returned eQTL variants (regulatory), while LLM-Query returned ClinVar variants (clinical significance). This represents complementary information.

### Patterns Observed

- **LLM-Query strengths**: Better at natural language interpretation, provides more contextual information, successfully answered coexpression and genomic element queries
- **MCP strengths**: More structured/precise outputs with specific identifiers, successful region searches, provides allele frequencies and annotations
- **Both failed**: Lupus variants (Q4), liver eQTL (Q7), Orphanet eQTLs (Q9), variant-gene links for specific SPDI (Q12)
- **Same results**: Disease associations (Q3), genomic elements for rs6994300 (Q10), eQTL status of rs6994300 (Q13)

### Error Rates
- MCP: 0 errors (but 5 "unable to answer" responses due to tool limitations)
- LLM-Query: 1 internal server error (Q6)
