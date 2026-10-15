"""Edge endpoint configuration for the IGVF Catalog API.

This module defines the structure and parameters for all edge (relationship) endpoints
in the IGVF Catalog API. It provides a centralized configuration that tools can use
to build correct queries with proper parameter names, source values, and filters.
"""

from typing import Literal, TypedDict

from .api_client import method_params

EntityType = Literal[
    'gene',
    'transcript',
    'protein',
    'variant',
    'ontology',
    'drug',
    'complex',
    'study',
    'pathway',
    'genomic_element',
    'coding_variant',
]


class EdgeEndpointConfig(TypedDict, total=False):
    """Configuration for an edge endpoint."""

    client_method: str  # AsyncIgvfCatalogApi method name
    path: str  # API path, for display
    from_type: EntityType
    to_type: EntityType
    from_params: list[str]  # Valid parameter names for the "from" entity
    sources: list[str]  # Data sources; valid `source` filter values where the endpoint accepts one
    labels: list[str]  # Valid label/edge type values
    methods: list[str]  # Valid method values
    filters: dict[str, str]  # Filter name -> type (range, string, enum)
    max_limit: int  # Maximum page size


GENE_PARAMS = ['gene_id', 'gene_name', 'hgnc_id', 'synonym']
PROTEIN_PARAMS = ['protein_id', 'protein_name', 'uniprot_name', 'uniprot_full_name', 'dbxrefs']
VARIANT_PARAMS = ['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id']

QTL_SOURCES = ['AFGR', 'EBI', 'IGVF']
QTL_LABELS = ['eQTL', 'spliceQTL', 'variant effect on gene expression']
QTL_METHODS = ['CRISPR screen', 'eQTL', 'spliceQTL']
QTL_FILTERS = {
    'neg_log10_pvalue': 'range',
    'effect_size': 'range',
    'biological_context': 'string',
    'files_fileset': 'string',
}

VARIANT_PROTEIN_SOURCES = ['ADASTRA', 'GVATdb', 'IGVF', 'UKB']
VARIANT_PROTEIN_LABELS = ['allele-specific binding', 'pQTL', 'predicted allele-specific binding']
VARIANT_PROTEIN_METHODS = ['ADASTRA', 'GVATdb', 'SEMVAR', 'pQTL']

PHENOTYPE_LABELS = [
    'GWAS',
    'predicted variant effect on phenotype',
    'protein variant effect',
    'variant effect on phenotype',
]
PHENOTYPE_METHODS = ['CRISPR screen', 'GWAS', 'SGE', 'cV2F']


# Methods of /genes/genes: COXPRESdb co-expression, or the BioGRID genetic interaction types
GENE_GENE_METHODS = [
    'COXPRESdb',
    'dosage growth defect (sensu BioGRID)',
    'dosage lethality (sensu BioGRID)',
    'dosage lethality (sensu BioGRID), phenotypic enhancement (sensu BioGRID)',
    'dosage lethality (sensu BioGRID), synthetic lethality (sensu BioGRID)',
    'dosage rescue (sensu BioGRID)',
    'dosage rescue (sensu BioGRID), phenotypic enhancement (sensu BioGRID)',
    'dosage rescue (sensu BioGRID), synthetic growth defect (sensu BioGRID)',
    'dosage rescue (sensu BioGRID), synthetic haploinsufficiency (sensu BioGRID)',
    'negative genetic interaction (sensu BioGRID)',
    'negative genetic interaction (sensu BioGRID), phenotypic suppression (sensu BioGRID)',
    'negative genetic interaction (sensu BioGRID), positive genetic interaction (sensu BioGRID)',
    'negative genetic interaction (sensu BioGRID), synthetic growth defect (sensu BioGRID)',
    'negative genetic interaction (sensu BioGRID), synthetic growth defect (sensu BioGRID), '
    'synthetic lethality (sensu BioGRID)',
    'negative genetic interaction (sensu BioGRID), synthetic lethality (sensu BioGRID)',
    'phenotypic enhancement (sensu BioGRID)',
    'phenotypic enhancement (sensu BioGRID), phenotypic suppression (sensu BioGRID)',
    'phenotypic enhancement (sensu BioGRID), phenotypic suppression (sensu BioGRID), '
    'synthetic haploinsufficiency (sensu BioGRID)',
    'phenotypic enhancement (sensu BioGRID), phenotypic suppression (sensu BioGRID), '
    'synthetic lethality (sensu BioGRID)',
    'phenotypic enhancement (sensu BioGRID), positive genetic interaction (sensu BioGRID)',
    'phenotypic enhancement (sensu BioGRID), synthetic growth defect (sensu BioGRID)',
    'phenotypic enhancement (sensu BioGRID), synthetic lethality (sensu BioGRID)',
    'phenotypic suppression (sensu BioGRID)',
    'positive genetic interaction (sensu BioGRID)',
    'positive genetic interaction (sensu BioGRID), synthetic lethality (sensu BioGRID)',
    'positive genetic interaction (sensu BioGRID), synthetic rescue (sensu BioGRID)',
    'synthetic growth defect (sensu BioGRID)',
    'synthetic growth defect (sensu BioGRID), synthetic lethality (sensu BioGRID)',
    'synthetic haploinsufficiency (sensu BioGRID)',
    'synthetic lethality (sensu BioGRID)',
    'synthetic rescue (sensu BioGRID)',
]

# Methods of /proteins/proteins: the interaction types
PROTEIN_PROTEIN_METHODS = [
    'acetylation reaction',
    'acetylation reaction, direct interaction',
    'adp ribosylation reaction',
    'adp ribosylation reaction, direct interaction',
    'adp ribosylation reaction, direct interaction, enzymatic reaction',
    'ampylation reaction',
    'association',
    'association, colocalization',
    'association, colocalization, direct interaction, physical association',
    'association, colocalization, physical association',
    'association, covalent binding',
    'association, direct interaction',
    'association, direct interaction, physical association',
    'association, direct interaction, protein cleavage',
    'association, disulfide bond',
    'association, hydroxylation reaction',
    'association, phosphorylation reaction',
    'association, physical association',
    'association, ubiquitination reaction',
    'atpase reaction',
    'cleavage reaction',
    'cleavage reaction, direct interaction',
    'cleavage reaction, enzymatic reaction',
    'cleavage reaction, protein cleavage',
    'colocalization',
    'colocalization, direct interaction',
    'colocalization, direct interaction, physical association',
    'colocalization, physical association',
    'covalent binding',
    'covalent binding, direct interaction',
    'de-ADP-ribosylation reaction',
    'deacetylation reaction',
    'deacetylation reaction, direct interaction',
    'demethylation reaction',
    'deneddylation reaction',
    'dephosphorylation reaction',
    'dephosphorylation reaction, direct interaction',
    'dephosphorylation reaction, physical association',
    'deubiquitination reaction',
    'direct interaction',
    'direct interaction, disulfide bond',
    'direct interaction, enzymatic reaction',
    'direct interaction, glycosylation reaction',
    'direct interaction, methylation reaction',
    'direct interaction, neddylation reaction',
    'direct interaction, phosphorylation reaction',
    'direct interaction, physical association',
    'direct interaction, proline isomerization  reaction',
    'direct interaction, protein cleavage',
    'direct interaction, proximity',
    'direct interaction, sumoylation reaction',
    'direct interaction, ubiquitination reaction',
    'disulfide bond',
    'disulfide bond, physical association',
    'dna cleavage',
    'enzymatic reaction',
    'glycosylation reaction',
    'gtpase reaction',
    'guanine nucleotide exchange factor reaction',
    'hydroxylation reaction',
    'lipid addition, myristoylation reaction',
    'lipoprotein cleavage reaction',
    'methylation reaction',
    'neddylation reaction',
    'oxidoreductase activity electron transfer reaction',
    'palmitoylation reaction',
    'phosphorylation reaction',
    'phosphorylation reaction, physical association',
    'phosphorylation reaction, protein cleavage',
    'phosphotransfer reaction',
    'physical association',
    'physical association, proximity',
    'physical association, self interaction',
    'protein cleavage',
    'proximity',
    'putative self interaction',
    'rna cleavage',
    'self interaction',
    'sumoylation reaction',
    'transglutamination reaction',
    'ubiquitination reaction',
]

# Labels of /proteins/proteins: the interaction detection methods
PROTEIN_PROTEIN_LABELS = [
    '3D electron microscopy',
    'Split renilla luciferase complementation',
    'acetylase assay',
    'adp ribosylase assay',
    'affinity chromatography technology',
    'affinity technology',
    'aggregation assay',
    'amplified luminescent proximity homogeneous assay',
    'ampylation assay',
    'anti bait coimmunoprecipitation',
    'anti tag coimmunoprecipitation',
    'antibody array',
    'array technology',
    'atomic force microscopy',
    'atpase assay',
    'avexis',
    'barcode fusion genetics two hybrid',
    'bead aggregation assay',
    'beta galactosidase complementation',
    'beta lactamase complementation',
    'bimolecular fluorescence complementation',
    'bio-layer interferometry',
    'biochemical',
    'bioluminescence resonance energy transfer',
    'biophysical',
    'biosensor',
    'blue native page',
    'chromatin immunoprecipitation array',
    'chromatin immunoprecipitation assay',
    'chromatography technology',
    'circular dichroism',
    'classical fluorescence spectroscopy',
    'cleavage assay',
    'coimmunoprecipitation',
    'comigration in gel electrophoresis',
    'comigration in non denaturing gel electrophoresis',
    'comigration in sds page',
    'competition binding',
    'confocal microscopy',
    'cosedimentation',
    'cosedimentation in solution',
    'cosedimentation through density gradient',
    'cross-linking study',
    'de-ADP-ribosylation assay',
    'deacetylase assay',
    'decarboxylation assay',
    'demethylase assay',
    'detection by mass spectrometry',
    'deubiquitinase assay',
    'differential scanning calorimetry',
    'dihydrofolate reductase reconstruction',
    'display technology',
    'dynamic light scattering',
    'electron diffraction',
    'electron microscopy',
    'electron microscopy 3D helical reconstruction',
    'electron microscopy 3D single particle reconstruction',
    'electron paramagnetic resonance',
    'electron tomography',
    'electrophoretic mobility shift assay',
    'electrophoretic mobility supershift assay',
    'electrophoretic mobility-based method',
    'enzymatic footprinting',
    'enzymatic study',
    'enzyme linked immunosorbent assay',
    'experimental interaction detection',
    'far western blotting',
    'field flow fractionation',
    'filamentous phage display',
    'filter binding',
    'filter trap assay',
    'fluorescence correlation spectroscopy',
    'fluorescence microscopy',
    'fluorescence polarization spectroscopy',
    'fluorescence recovery after photobleaching',
    'fluorescence technology',
    'fluorescence-activated cell sorting',
    'fluorescent resonance energy transfer',
    'footprinting',
    'force spectroscopy',
    'gal4 vp16 complementation',
    'gdp/gtp exchange assay',
    'glycosylase assay',
    'gtpase assay',
    'homogeneous time resolved fluorescence',
    'hydroxylase assay',
    'imaging technique',
    'immunodepleted coimmunoprecipitation',
    'in-gel kinase assay',
    'inference by socio-affinity scoring',
    'infrared spectroscopy',
    'interaction detection method',
    'interactome parallel affinity capture',
    'ion exchange chromatography',
    'ion mobility mass spectrometry of complexes',
    'isothermal titration calorimetry',
    'kinase homogeneous time resolved fluorescence',
    'kinase scintillation proximity assay',
    'lambda phage display',
    'lambda repressor two hybrid',
    'lex-a dimerization assay',
    'lexa b52 complementation',
    'lexa vp16 complementation',
    'light microscopy',
    'light scattering',
    'lipoprotein cleavage assay',
    'luminescence based mammalian interactome mapping',
    'mammalian protein protein interaction trap',
    'mass spectrometry studies of complexes',
    'mass spectrometry study of hydrogen/deuterium exchange',
    'methyltransferase assay',
    'methyltransferase radiometric assay',
    'microscale thermophoresis',
    'molecular sieving',
    'mrna display',
    'myristoylase assay',
    'neddylase assay',
    'nuclear magnetic resonance',
    'nuclease assay',
    'oxidase assay',
    'oxidoreductase assay',
    'p8 filamentous phage display',
    'palmitoylase assay',
    'peptide array',
    'phage display',
    'phosphatase assay',
    'phosphotransferase assay',
    'polymerization',
    'probe interaction assay',
    'protease accessibility laddering',
    'protease assay',
    'protein array',
    'protein complementation assay',
    'protein cross-linking with a bifunctional reagent',
    'protein kinase assay',
    'protein phosphatase assay',
    'protein three hybrid',
    'proteinchip(r) on a surface-enhanced laser desorption/ionization',
    'proximity labelling technology',
    'proximity ligation assay',
    'proximity-dependent biotin identification',
    'pull down',
    'reverse phase chromatography',
    'reverse ras recruitment system',
    'reverse two hybrid',
    'ribonuclease assay',
    'rna immunoprecipitation',
    'rna interference',
    'sandwich immunoassay',
    'saturation binding',
    'scanning electron microscopy',
    'scintillation proximity assay',
    'small angle neutron scattering',
    'solid phase assay',
    'solid state nmr',
    'solution state nmr',
    'split firefly luciferase complementation',
    'split luciferase complementation',
    'static light scattering',
    'sumoylase assay',
    'super-resolution microscopy',
    'surface plasmon resonance',
    'surface plasmon resonance array',
    't7 phage display',
    'tandem affinity purification',
    'thermal shift binding',
    'three hybrid',
    'tox-r dimerization assay',
    'transcriptional complementation assay',
    'transmission electron microscopy',
    'two hybrid',
    'two hybrid array',
    'two hybrid bait and prey pooling approach',
    'two hybrid fragment pooling approach',
    'two hybrid pooling approach',
    'two hybrid prey pooling approach',
    'ubiquitin reconstruction',
    'ubiquitinase assay',
    'ultraviolet-visible spectroscopy',
    'unspecified method',
    'validated two hybrid',
    'virotrap',
    'x ray scattering',
    'x-ray crystallography',
    'x-ray fiber diffraction',
    'yeast display',
    'zymography',
]

# Complete edge endpoint registry
EDGE_ENDPOINTS: dict[str, EdgeEndpointConfig] = {
    # Variant-Gene relationships (eQTLs, sQTLs, CRISPR screens)
    'variants_genes': {
        'client_method': 'genes_from_variants',
        'path': '/variants/genes',
        'from_type': 'variant',
        'to_type': 'gene',
        'from_params': VARIANT_PARAMS,
        'sources': QTL_SOURCES,
        'labels': QTL_LABELS,
        'methods': QTL_METHODS,
        'filters': QTL_FILTERS,
        'max_limit': 500,
    },
    'genes_variants': {
        'client_method': 'variants_from_genes',
        'path': '/genes/variants',
        'from_type': 'gene',
        'to_type': 'variant',
        'from_params': GENE_PARAMS,
        'sources': QTL_SOURCES,
        'labels': QTL_LABELS,
        'methods': QTL_METHODS,
        'filters': QTL_FILTERS,
        'max_limit': 500,
    },
    # Variant-Protein relationships (pQTL, allele-specific binding)
    'variants_proteins': {
        'client_method': 'proteins_from_variants',
        'path': '/variants/proteins',
        'from_type': 'variant',
        'to_type': 'protein',
        'from_params': VARIANT_PARAMS + ['region'],
        'sources': VARIANT_PROTEIN_SOURCES,
        'labels': VARIANT_PROTEIN_LABELS,
        'methods': VARIANT_PROTEIN_METHODS,
        'filters': {
            'files_fileset': 'string',
        },
        'max_limit': 100,
    },
    'proteins_variants': {
        'client_method': 'variants_from_proteins',
        'path': '/proteins/variants',
        'from_type': 'protein',
        'to_type': 'variant',
        'from_params': PROTEIN_PARAMS,
        'sources': VARIANT_PROTEIN_SOURCES,
        'labels': VARIANT_PROTEIN_LABELS,
        'methods': VARIANT_PROTEIN_METHODS,
        'filters': {
            'files_fileset': 'string',
        },
        'max_limit': 100,
    },
    # Variant-Phenotype relationships (GWAS)
    'variants_phenotypes': {
        'client_method': 'phenotypes_from_variants',
        'path': '/variants/phenotypes',
        'from_type': 'variant',
        'to_type': 'ontology',
        'from_params': VARIANT_PARAMS + ['region'],
        'sources': ['OpenTargets', 'IGVF'],
        'labels': PHENOTYPE_LABELS,
        'methods': PHENOTYPE_METHODS,
        'filters': {
            'neg_log10_pvalue': 'range',
            'phenotype_id': 'string',
            'files_fileset': 'string',
        },
        'max_limit': 100,
    },
    'phenotypes_variants': {
        'client_method': 'variants_from_phenotypes',
        'path': '/phenotypes/variants',
        'from_type': 'ontology',
        'to_type': 'variant',
        'from_params': ['phenotype_id', 'phenotype_name'],
        'sources': ['IGVF', 'OpenTargets'],
        'labels': PHENOTYPE_LABELS,
        'methods': PHENOTYPE_METHODS,
        'filters': {
            'neg_log10_pvalue': 'range',
            'files_fileset': 'string',
        },
        'max_limit': 100,
    },
    # Variant-Drug relationships (PharmGKB)
    'variants_drugs': {
        'client_method': 'drugs_from_variants',
        'path': '/variants/drugs',
        'from_type': 'variant',
        'to_type': 'drug',
        'from_params': VARIANT_PARAMS,
        'sources': ['PharmGKB'],
        'filters': {
            'pmid': 'string',
            'phenotype_categories': 'enum',
        },
        'max_limit': 100,
    },
    'drugs_variants': {
        'client_method': 'variants_from_drugs',
        'path': '/drugs/variants',
        'from_type': 'drug',
        'to_type': 'variant',
        'from_params': ['drug_id', 'drug_name'],
        'sources': ['PharmGKB'],
        'filters': {
            'pmid': 'string',
            'phenotype_categories': 'enum',
        },
        'max_limit': 100,
    },
    # Variant-Disease relationships (ClinGen)
    'variants_diseases': {
        'client_method': 'disease_from_variants',
        'path': '/variants/diseases',
        'from_type': 'variant',
        'to_type': 'ontology',
        'from_params': VARIANT_PARAMS,
        'sources': ['ClinGen'],
        'filters': {
            'assertion': 'enum',
            'pmid': 'string',
        },
        'max_limit': 100,
    },
    # Gene-Disease relationships (Orphanet, ClinGen, GenCC)
    'genes_diseases': {
        'client_method': 'diseases_from_genes',
        'path': '/genes/diseases',
        'from_type': 'gene',
        'to_type': 'ontology',
        'from_params': GENE_PARAMS,
        'sources': ['GenCC', 'Orphanet', 'ClinGen'],
        'filters': {},
        'max_limit': 25,
    },
    'diseases_genes': {
        'client_method': 'genes_from_diseases',
        'path': '/diseases/genes',
        'from_type': 'ontology',
        'to_type': 'gene',
        'from_params': ['disease_id', 'disease_name'],
        'sources': ['GenCC', 'Orphanet'],
        'filters': {},
        'max_limit': 100,
    },
    # Gene-Gene relationships (coexpression, interactions)
    'genes_genes': {
        'client_method': 'genes_genes',
        'path': '/genes/genes',
        'from_type': 'gene',
        'to_type': 'gene',
        'from_params': GENE_PARAMS,
        'sources': ['BioGRID', 'COXPRESdb'],
        'labels': ['co-expression', 'genetic interference'],
        'methods': GENE_GENE_METHODS,
        'filters': {
            'z_score': 'range',
            'interaction_type': 'enum',
        },
        'max_limit': 100,
    },
    # Protein-Protein interactions
    'proteins_proteins': {
        'client_method': 'proteins_proteins',
        'path': '/proteins/proteins',
        'from_type': 'protein',
        'to_type': 'protein',
        'from_params': PROTEIN_PARAMS,
        'sources': ['BioGRID', 'BioGRID; IntAct', 'IntAct'],
        'labels': PROTEIN_PROTEIN_LABELS,
        'methods': PROTEIN_PROTEIN_METHODS,
        'filters': {
            'interaction_type': 'enum',
        },
        'max_limit': 250,
    },
    # Complex-Protein relationships
    'complexes_proteins': {
        'client_method': 'proteins_from_complexes',
        'path': '/complexes/proteins',
        'from_type': 'complex',
        'to_type': 'protein',
        'from_params': ['complex_id', 'complex_name', 'description'],
        'sources': ['EBI Complex Portal'],
        'filters': {},
        'max_limit': 50,
    },
    'proteins_complexes': {
        'client_method': 'complexes_from_proteins',
        'path': '/proteins/complexes',
        'from_type': 'protein',
        'to_type': 'complex',
        # dbxrefs only narrows a query here; on its own the API requires protein_id, name, uniprot_name or
        # uniprot_full_name, so a bare UniProt accession is resolved to its UniProt name instead
        'from_params': [p for p in PROTEIN_PARAMS if p != 'dbxrefs'],
        'sources': ['EBI Complex Portal'],
        'filters': {},
        'max_limit': 100,
    },
    # Gene-Pathway relationships
    'genes_pathways': {
        'client_method': 'pathways_from_genes',
        'path': '/genes/pathways',
        'from_type': 'gene',
        'to_type': 'pathway',
        'from_params': GENE_PARAMS,
        'sources': ['Reactome'],
        'filters': {},
        'max_limit': 500,
    },
    # Gene-Transcript relationships
    'genes_transcripts': {
        'client_method': 'transcripts_from_genes',
        'path': '/genes/transcripts',
        'from_type': 'gene',
        'to_type': 'transcript',
        'from_params': GENE_PARAMS,
        'sources': ['GENCODE'],
        'filters': {},
        'max_limit': 100,
    },
    'transcripts_genes': {
        'client_method': 'genes_from_transcripts',
        'path': '/transcripts/genes',
        'from_type': 'transcript',
        'to_type': 'gene',
        'from_params': ['transcript_id', 'region'],
        'sources': ['GENCODE'],
        'filters': {},
        'max_limit': 100,
    },
    # Transcript-Protein relationships
    'transcripts_proteins': {
        'client_method': 'proteins_from_transcripts',
        'path': '/transcripts/proteins',
        'from_type': 'transcript',
        'to_type': 'protein',
        'from_params': ['transcript_id', 'transcript_type', 'region'],
        'sources': ['GENCODE'],
        'filters': {},
        'max_limit': 100,
    },
    'proteins_transcripts': {
        'client_method': 'transcripts_from_proteins',
        'path': '/proteins/transcripts',
        'from_type': 'protein',
        'to_type': 'transcript',
        'from_params': PROTEIN_PARAMS,
        'sources': ['GENCODE'],
        'filters': {},
        'max_limit': 100,
    },
    # Motif-Protein relationships
    'motifs_proteins': {
        'client_method': 'proteins_from_motifs',
        'path': '/motifs/proteins',
        'from_type': 'ontology',
        'to_type': 'protein',
        'from_params': ['tf_name'],
        'sources': ['IGVF', 'HOCOMOCOv11'],
        'methods': ['HOCOMOCO', 'SEMpl'],
        'filters': {
            'files_fileset': 'string',
        },
        'max_limit': 1000,
    },
    'proteins_motifs': {
        'client_method': 'motifs_from_proteins',
        'path': '/proteins/motifs',
        'from_type': 'protein',
        'to_type': 'ontology',
        'from_params': PROTEIN_PARAMS,
        'sources': ['IGVF', 'HOCOMOCOv11'],
        'methods': ['HOCOMOCO', 'SEMpl'],
        'filters': {
            'files_fileset': 'string',
        },
        'max_limit': 1000,
    },
    # Variant-Variant relationships (Linkage Disequilibrium)
    'variants_variants': {
        'client_method': 'variants_from_variant_id',
        'path': '/variants/variant-ld',
        'from_type': 'variant',
        'to_type': 'variant',
        'from_params': VARIANT_PARAMS + ['region'],
        'sources': ['TopLD'],
        'filters': {
            'r2': 'range',
            'd_prime': 'range',
            'ancestry': 'enum',
        },
        'max_limit': 500,
    },
    # Variant-Coding Variant relationships
    'variants_coding_variants': {
        'client_method': 'coding_variants_from_variants',
        'path': '/variants/coding-variants',
        'from_type': 'variant',
        'to_type': 'coding_variant',
        'from_params': ['variant_id', 'spdi', 'hgvs', 'ca_id'],
        'sources': ['dbNSFP'],
        'filters': {},
        'max_limit': 500,
    },
    'coding_variants_variants': {
        'client_method': 'variants_from_coding_variants',
        'path': '/coding-variants/variants',
        'from_type': 'coding_variant',
        'to_type': 'variant',
        'from_params': ['coding_variant_name', 'hgvsp'],
        'sources': ['dbNSFP'],
        'filters': {},
        'max_limit': 500,
    },
    # Variant-Genomic Element relationships (caQTL)
    'variants_genomic_elements': {
        'client_method': 'genomic_elements_from_variants',
        'path': '/variants/genomic-elements',
        'from_type': 'variant',
        'to_type': 'genomic_element',
        'from_params': VARIANT_PARAMS,
        'sources': ['AFGR', 'IGVF'],
        'methods': ['caQTL'],
        'filters': {
            'biological_context': 'string',
            'files_fileset': 'string',
        },
        'max_limit': 300,
    },
    # Genomic Element-Gene relationships (E2G predictions, CRISPR screens)
    'genomic_elements_genes': {
        'client_method': 'genes_from_genomic_elements',
        'path': '/genomic-elements/genes',
        'from_type': 'genomic_element',
        'to_type': 'gene',
        'from_params': ['region'],
        'sources': ['ENCODE', 'IGVF'],
        'methods': ['CRISPR screen', 'ENCODE-rE2G', 'Perturb-seq', 'scE2G'],
        'filters': {
            'source_annotation': 'enum',
            'region_type': 'enum',
            'biosample_term': 'string',
            'biological_context': 'string',
            'neg_log10_pvalue': 'range',
            'score': 'range',
            'files_fileset': 'string',
        },
        'max_limit': 500,
    },
    # Gene-Genomic Element relationships (E2G predictions, CRISPR screens), queried from the gene side
    'genes_genomic_elements': {
        'client_method': 'genomic_elements_from_genes',
        'path': '/genes/genomic-elements',
        'from_type': 'gene',
        'to_type': 'genomic_element',
        'from_params': GENE_PARAMS,
        'sources': ['ENCODE', 'IGVF'],
        'methods': ['CRISPR screen', 'ENCODE-rE2G', 'Perturb-seq', 'scE2G'],
        'filters': {
            'biosample_term': 'string',
            'biological_context': 'string',
            'neg_log10_pvalue': 'range',
            'score': 'range',
            'files_fileset': 'string',
        },
        'max_limit': 500,
    },
    # Genomic Element-Biosample relationships (MPRA)
    'genomic_elements_biosamples': {
        'client_method': 'biosamples_from_genomic_elements',
        'path': '/genomic-elements/biosamples',
        'from_type': 'genomic_element',
        'to_type': 'ontology',
        'from_params': ['region'],
        'sources': ['ENCODE', 'IGVF'],
        'methods': ['MPRA'],
        'filters': {
            'region_type': 'enum',
            'files_fileset': 'string',
        },
        'max_limit': 50,
    },
    'biosamples_genomic_elements': {
        'client_method': 'genomic_elements_from_biosamples',
        'path': '/biosamples/genomic-elements',
        'from_type': 'ontology',
        'to_type': 'genomic_element',
        'from_params': ['biosample_name'],
        'sources': ['ENCODE', 'IGVF'],
        'methods': ['MPRA'],
        'filters': {
            'files_fileset': 'string',
        },
        'max_limit': 50,
    },
    # GO term annotations
    'go_terms_annotations': {
        'client_method': 'go_terms_from_annotations',
        'path': '/gene-products/go-terms',
        'from_type': 'protein',
        'to_type': 'ontology',
        'from_params': ['query'],  # Can be protein or transcript ID
        'sources': ['Gene Ontology'],
        'filters': {
            'name': 'enum',  # 'involved in', 'is located in', 'has the function'
        },
        'max_limit': 100,
    },
}


# Relationship type to endpoint mapping for higher-level abstractions
RELATIONSHIP_TYPE_MAPPING = {
    'regulatory': {
        'gene': ['genes_variants', 'genes_genomic_elements'],
        'variant': ['variants_genes', 'variants_genomic_elements'],
        'genomic_element': ['genomic_elements_genes'],
    },
    'genetic': {
        'gene': ['genes_diseases'],
        'variant': ['variants_phenotypes', 'variants_diseases'],
        'ontology': ['phenotypes_variants', 'diseases_genes'],
    },
    'physical': {
        'protein': ['proteins_proteins', 'proteins_complexes'],
        'complex': ['complexes_proteins'],
        'gene': ['genes_genes'],
    },
    'functional': {
        'gene': ['genes_pathways'],
        'protein': ['go_terms_annotations'],
    },
    'pharmacological': {
        'variant': ['variants_drugs'],
        'drug': ['drugs_variants'],
    },
    'ld': {
        'variant': ['variants_variants'],
    },
    'coding': {
        'variant': ['variants_coding_variants'],
        'coding_variant': ['coding_variants_variants'],
    },
    'transcription': {
        'gene': ['genes_transcripts'],
        'transcript': ['transcripts_genes', 'transcripts_proteins'],
        'protein': ['proteins_transcripts'],
    },
}


def get_edge_config(endpoint_key: str) -> EdgeEndpointConfig | None:
    """Get configuration for a specific edge endpoint."""
    return EDGE_ENDPOINTS.get(endpoint_key)


def supports_verbose(config: EdgeEndpointConfig) -> bool:
    """Whether the endpoint's client method accepts the verbose parameter."""
    return 'verbose' in method_params(config['client_method'])


def get_endpoints_for_entity_and_relationship(
    entity_type: EntityType, relationship_type: str
) -> list[str]:
    """
    Get applicable endpoint keys for an entity type and relationship type.

    Args:
        entity_type: Type of the starting entity
        relationship_type: Type of relationship to find

    Returns:
        List of endpoint keys that match the criteria
    """
    if relationship_type not in RELATIONSHIP_TYPE_MAPPING:
        return []

    entity_mapping = RELATIONSHIP_TYPE_MAPPING[relationship_type]
    return entity_mapping.get(entity_type, [])


def get_all_sources() -> set[str]:
    """Get all unique data sources across all endpoints."""
    sources = set()
    for config in EDGE_ENDPOINTS.values():
        if 'sources' in config:
            sources.update(config['sources'])
    return sources


def get_sources_by_category() -> dict[str, list[str]]:
    """Organize sources by category for the list_sources tool."""
    return {
        'variant_annotations': ['dbNSFP', 'ClinGen'],
        'gene_expression': ['AFGR', 'EBI', 'IGVF'],
        'regulatory': ['ADASTRA', 'GVATdb', 'UKB', 'ENCODE', 'IGVF'],
        'disease': ['Orphanet', 'ClinGen', 'GenCC', 'OpenTargets'],
        'drugs': ['PharmGKB'],
        'interactions': ['BioGRID', 'IntAct', 'COXPRESdb', 'EBI Complex Portal'],
        'studies': ['GWAS Catalog', 'OpenTargets'],
        'structure': ['GENCODE'],
        'linkage': ['TopLD'],
        'motifs': ['HOCOMOCOv11', 'IGVF'],
        'pathways': ['Reactome'],
        'ontology': ['Gene Ontology'],
    }
