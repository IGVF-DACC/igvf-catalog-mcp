"""Genomic region parser with flexible format support."""

import re
from decimal import Decimal, localcontext
from typing import NamedTuple

# Number part of a position: digits, optionally with commas between groups of three, and an optional decimal part
POSITION_NUMBER = r'^(?=\.?\d)(\d+|\d{1,3}(,\d{3})+)?(\.\d*)?$'


class GenomicRegion(NamedTuple):
    """Parsed genomic region."""

    chromosome: str
    start: int
    end: int
    # End position as given, when it was beyond the end of the chromosome and end was clipped to the chromosome length
    requested_end: str | None = None

    def __str__(self) -> str:
        """Format as chr:start-end."""
        return f'{self.chromosome}:{self.start}-{self.end}'


class RegionParser:
    """Parse and normalize genomic region formats."""

    # Value of each position suffix
    MULTIPLIERS = {'K': 1_000, 'M': 1_000_000, 'G': 1_000_000_000}

    # Number of autosomes per organism; each organism also has chrX, chrY and chrM
    AUTOSOMES = {'Homo sapiens': 22, 'Mus musculus': 19}

    # Valid normalized chromosome names per organism
    VALID_CHROMOSOMES = {
        organism: {f'chr{number}' for number in range(1, count + 1)} | {'chrX', 'chrY', 'chrM'}
        for organism, count in AUTOSOMES.items()
    }

    # Reference assembly of each organism in the catalog
    ASSEMBLIES = {'Homo sapiens': 'GRCh38', 'Mus musculus': 'GRCm39'}

    # Chromosome lengths in bp, from the UCSC hg38 and mm39 chrom.sizes files (GRCh38 and GRCm39)
    CHROMOSOME_LENGTHS = {
        'Homo sapiens': {
            'chr1': 248_956_422,
            'chr2': 242_193_529,
            'chr3': 198_295_559,
            'chr4': 190_214_555,
            'chr5': 181_538_259,
            'chr6': 170_805_979,
            'chr7': 159_345_973,
            'chr8': 145_138_636,
            'chr9': 138_394_717,
            'chr10': 133_797_422,
            'chr11': 135_086_622,
            'chr12': 133_275_309,
            'chr13': 114_364_328,
            'chr14': 107_043_718,
            'chr15': 101_991_189,
            'chr16': 90_338_345,
            'chr17': 83_257_441,
            'chr18': 80_373_285,
            'chr19': 58_617_616,
            'chr20': 64_444_167,
            'chr21': 46_709_983,
            'chr22': 50_818_468,
            'chrX': 156_040_895,
            'chrY': 57_227_415,
            'chrM': 16_569,
        },
        'Mus musculus': {
            'chr1': 195_154_279,
            'chr2': 181_755_017,
            'chr3': 159_745_316,
            'chr4': 156_860_686,
            'chr5': 151_758_149,
            'chr6': 149_588_044,
            'chr7': 144_995_196,
            'chr8': 130_127_694,
            'chr9': 124_359_700,
            'chr10': 130_530_862,
            'chr11': 121_973_369,
            'chr12': 120_092_757,
            'chr13': 120_883_175,
            'chr14': 125_139_656,
            'chr15': 104_073_951,
            'chr16': 98_008_968,
            'chr17': 95_294_699,
            'chr18': 90_720_763,
            'chr19': 61_420_004,
            'chrX': 169_476_592,
            'chrY': 91_455_967,
            'chrM': 16_299,
        },
    }

    @classmethod
    def parse_region(cls, region: str, organism: str = 'Homo sapiens') -> GenomicRegion:
        """
        Parse a genomic region string into structured components.

        Supports flexible formats:
        - chr1:1000000-2000000
        - 1:1000000-2000000
        - chr1:1,000,000-2,000,000 (commas)
        - chrX:1M-2M (M notation for millions)
        - chrX:1.5M-2.5M (decimal M notation)

        Positions are 0-based and the end is exclusive. The start must be within the chromosome; an end beyond
        the end of the chromosome is clipped to the chromosome length, and the requested end is kept in
        requested_end.

        Args:
            region: Region string to parse
            organism: Organism whose chromosomes are valid ('Homo sapiens' or 'Mus musculus')

        Returns:
            GenomicRegion with normalized chromosome, start, and end

        Raises:
            ValueError: If region format is invalid, the chromosome does not exist in the organism or the start
                position is beyond the end of the chromosome
        """
        # Remove whitespace
        region = region.strip()

        # Basic format: chr:start-end
        match = re.match(
            r'^(chr)?([0-9]{1,2}|[XYM]):([\d,\.]+[KMG]?)-([\d,\.]+[KMG]?)$', region, re.IGNORECASE)

        if not match:
            raise ValueError(
                f"Invalid region format: '{region}'. "
                f"Expected format: 'chr1:1000-2000' or '1:1000-2000'. "
                f'The colon separates chromosome from position range.'
            )

        chr_prefix, chr_name, start_str, end_str = match.groups()

        # Normalize chromosome name
        chromosome = cls._normalize_chromosome(
            chr_name, chr_prefix is not None)
        cls._validate_chromosome(chromosome, organism)

        # Parse positions with support for notations
        start = cls._parse_position(start_str)
        end = cls._parse_position(end_str)

        # Validate positions
        length = cls.CHROMOSOME_LENGTHS[organism][chromosome]
        if start >= length:
            raise ValueError(
                f"Invalid region: start position '{start_str}' is beyond the end of {chromosome} "
                f'({length:,} bp in {cls.ASSEMBLIES[organism]}; the largest start position is {length - 1})'
            )

        if start >= end:
            raise ValueError(
                f'Invalid region: start position ({start}) must be less than end position ({end})'
            )

        if start < 0:
            raise ValueError(
                f'Invalid region: start position ({start}) cannot be negative')

        if end > length:
            return GenomicRegion(chromosome=chromosome, start=start, end=length, requested_end=end_str)

        return GenomicRegion(chromosome=chromosome, start=start, end=end)

    @classmethod
    def _normalize_chromosome(cls, chr_name: str, has_prefix: bool) -> str:
        """
        Normalize chromosome name to 'chrN' format.

        Args:
            chr_name: Chromosome name or number
            has_prefix: Whether the input already had 'chr' prefix

        Returns:
            Normalized chromosome name with 'chr' prefix
        """
        # Convert to lowercase for comparison
        chr_lower = chr_name.lower()

        # Normalize to uppercase for X, Y, M
        if chr_lower in ('x', 'y', 'm'):
            chr_name = chr_lower.upper()

        # Add chr prefix if not present
        if not has_prefix:
            return f'chr{chr_name}'

        return f'chr{chr_name}'

    @classmethod
    def _validate_chromosome(cls, chromosome: str, organism: str) -> None:
        """
        Check that a normalized chromosome name exists in an organism.

        Args:
            chromosome: Normalized chromosome name (e.g., 'chr1', 'chrX')
            organism: Organism name

        Raises:
            ValueError: If the organism is unknown or does not have the chromosome
        """
        if organism not in cls.VALID_CHROMOSOMES:
            raise ValueError(
                f"Unknown organism: '{organism}'. Valid: {', '.join(cls.VALID_CHROMOSOMES)}")

        if chromosome not in cls.VALID_CHROMOSOMES[organism]:
            raise ValueError(
                f"Invalid chromosome '{chromosome}' for {organism}. "
                f'Valid: chr1-chr{cls.AUTOSOMES[organism]}, chrX, chrY, chrM'
            )

    @classmethod
    def _parse_position(cls, position_str: str) -> int:
        """
        Parse a position string, handling commas and K/M/G notation.

        The value is computed exactly, so it must be a whole number of base pairs.

        Args:
            position_str: Position string (e.g., "1000000", "1,000,000", "1M", "1.5M")

        Returns:
            Position as integer

        Raises:
            ValueError: If position format is invalid or the position is not a whole number
        """
        number, multiplier = position_str, 1
        suffix = position_str[-1:].upper()
        if suffix in cls.MULTIPLIERS:
            number, multiplier = position_str[:-1], cls.MULTIPLIERS[suffix]

        if not re.match(POSITION_NUMBER, number):
            raise ValueError(
                f"Invalid position format: '{position_str}'. Use digits, optionally with commas between groups of "
                "three (e.g. '1,000,000'), or a number with a K, M or G suffix (e.g. '1.5M')"
            )

        digits = number.replace(',', '')
        with localcontext() as context:
            context.prec = len(digits) + len(str(multiplier))
            position = Decimal(digits) * multiplier
            if position != position.to_integral_value():
                raise ValueError(
                    f"Invalid position: '{position_str}' is {position.normalize():f} bp, "
                    'not a whole number of base pairs'
                )

        return int(position)

    @classmethod
    def validate_region_size(cls, region: GenomicRegion, max_size: int) -> None:
        """
        Validate that a region is not too large.

        Args:
            region: The genomic region to validate
            max_size: Maximum allowed size in base pairs

        Raises:
            ValueError: If region is too large
        """
        size = region.end - region.start
        if size > max_size:
            raise ValueError(
                f'Region size ({size:,} bp) exceeds maximum allowed size ({max_size:,} bp)'
            )
