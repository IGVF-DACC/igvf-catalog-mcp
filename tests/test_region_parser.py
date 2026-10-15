"""Tests for region parser."""

import re

import pytest

from igvf_catalog_mcp.services.region_parser import GenomicRegion, RegionParser


def test_parse_basic_region():
    """Test parsing of basic region format."""
    region = RegionParser.parse_region('chr1:1000-2000')
    assert region.chromosome == 'chr1'
    assert region.start == 1000
    assert region.end == 2000


def test_parse_without_chr_prefix():
    """Test parsing region without 'chr' prefix."""
    region = RegionParser.parse_region('1:1000-2000')
    assert region.chromosome == 'chr1'
    assert region.start == 1000
    assert region.end == 2000


def test_parse_with_commas():
    """Test parsing region with comma separators."""
    region = RegionParser.parse_region('chr1:1,000,000-2,000,000')
    assert region.chromosome == 'chr1'
    assert region.start == 1000000
    assert region.end == 2000000


def test_parse_with_m_notation():
    """Test parsing region with M (million) notation."""
    region = RegionParser.parse_region('chr1:1M-2M')
    assert region.chromosome == 'chr1'
    assert region.start == 1000000
    assert region.end == 2000000


def test_parse_with_decimal_m():
    """Test parsing region with decimal M notation."""
    region = RegionParser.parse_region('chr1:1.5M-2.5M')
    assert region.chromosome == 'chr1'
    assert region.start == 1500000
    assert region.end == 2500000


@pytest.mark.parametrize('whole', [0, 1, 2, 9, 17, 49, 100, 248])
def test_decimal_m_notation_is_exact(whole):
    """Test that every a.bbbM position is the exact number of base pairs."""
    expected = {f'{whole}.{thousandths:03d}M': whole * 1_000_000 + thousandths * 1_000 for thousandths in range(1000)}
    assert {position: RegionParser._parse_position(position) for position in expected} == expected


@pytest.mark.parametrize('whole', [0, 1, 9, 10, 999, 12345, 248956])
def test_decimal_k_notation_is_exact(whole):
    """Test that every a.bbK position is the exact number of base pairs."""
    expected = {f'{whole}.{hundredths:02d}k': whole * 1_000 + hundredths * 10 for hundredths in range(100)}
    assert {position: RegionParser._parse_position(position) for position in expected} == expected


@pytest.mark.parametrize(
    ('position', 'expected'),
    [
        ('1.001K', 1001),
        ('1.000001M', 1000001),
        ('0.000000001G', 1),
        ('2.5G', 2_500_000_000),
        ('.5M', 500_000),
        ('1000.0', 1000),
        ('1,000.5K', 1_000_500),
        ('12,345,678', 12_345_678),
    ],
)
def test_parse_position_exact(position, expected):
    """Test that positions with suffixes, decimals and commas are exact."""
    assert RegionParser._parse_position(position) == expected


@pytest.mark.parametrize(
    ('position', 'expected'),
    [
        ('123456789012345678901234567891', 123456789012345678901234567891),
        ('123,456,789,012,345,678,901,234,567,891', 123456789012345678901234567891),
        ('123456789012345678901234567.891K', 123456789012345678901234567891),
        ('9' * 40 + 'K', int('9' * 40) * 1_000),
    ],
)
def test_parse_position_with_many_digits_is_exact(position, expected):
    """Test that positions with more digits than the default decimal precision are not rounded."""
    assert RegionParser._parse_position(position) == expected


@pytest.mark.parametrize(
    ('position', 'bp'),
    [
        ('1.0000000000000000000000000001M', '1000000.0000000000000000000001'),
        ('123456789012345678901234567891.5', '123456789012345678901234567891.5'),
        ('1.0000000000000000000000000000000000001G', '1000000000.0000000000000000000000000001'),
    ],
)
def test_position_with_many_digits_must_be_whole_number(position, bp):
    """Test that a fractional position is rejected even when it has more digits than the default precision."""
    message = rf"^Invalid position: '{re.escape(position)}' is {re.escape(bp)} bp, not a whole number of base pairs$"
    with pytest.raises(ValueError, match=message):
        RegionParser._parse_position(position)


def test_parse_decimal_m_region_is_exact():
    """Test that a decimal M end position is not rounded down."""
    assert str(RegionParser.parse_region('chrX:1M-1.001M')) == 'chrX:1000000-1001000'


@pytest.mark.parametrize(
    ('position', 'bp'),
    [('1.0000001M', '1000000.1'), ('1.5', '1.5'), ('0.0005K', '0.5'), ('1.0000000001G', '1000000000.1')],
)
def test_position_must_be_whole_number(position, bp):
    """Test that a position that is not a whole number of base pairs raises ValueError."""
    message = rf"^Invalid position: '{re.escape(position)}' is {re.escape(bp)} bp, not a whole number of base pairs$"
    with pytest.raises(ValueError, match=message):
        RegionParser.parse_region(f'chr1:{position}-2G')


@pytest.mark.parametrize('position', ['1,5M', '1,00', '10,00,000', ',1000', '1000,', '.', '1..2', '1.2.3', ',M'])
def test_invalid_position_format(position):
    """Test that misplaced commas and points raise ValueError instead of being dropped."""
    with pytest.raises(ValueError, match=rf"^Invalid position format: '{re.escape(position)}'\."):
        RegionParser.parse_region(f'chr1:{position}-2G')


def test_parse_with_k_notation():
    """Test parsing region with K (thousand) notation."""
    region = RegionParser.parse_region('chr1:1K-2K')
    assert region.chromosome == 'chr1'
    assert region.start == 1000
    assert region.end == 2000


def test_parse_chrx():
    """Test parsing X chromosome."""
    region = RegionParser.parse_region('chrX:1000-2000')
    assert region.chromosome == 'chrX'

    region = RegionParser.parse_region('X:1000-2000')
    assert region.chromosome == 'chrX'


def test_parse_chry():
    """Test parsing Y chromosome."""
    region = RegionParser.parse_region('chrY:1000-2000')
    assert region.chromosome == 'chrY'

    region = RegionParser.parse_region('y:1000-2000')
    assert region.chromosome == 'chrY'


def test_parse_chrm():
    """Test parsing mitochondrial chromosome."""
    region = RegionParser.parse_region('chrM:1000-2000')
    assert region.chromosome == 'chrM'


@pytest.mark.parametrize('region', ['chr23:1-500', 'chr0:1000-2000', '99:1M-2M', 'chr01:1000-2000'])
def test_invalid_human_chromosome(region):
    """Test that chromosomes the human genome does not have raise ValueError."""
    with pytest.raises(ValueError, match=r"^Invalid chromosome 'chr\d+' for Homo sapiens\. "
                       r'Valid: chr1-chr22, chrX, chrY, chrM$'):
        RegionParser.parse_region(region)


def test_invalid_mouse_chromosome():
    """Test that human-only autosomes are invalid for mouse."""
    with pytest.raises(ValueError, match=r"^Invalid chromosome 'chr22' for Mus musculus\. "
                       r'Valid: chr1-chr19, chrX, chrY, chrM$'):
        RegionParser.parse_region('chr22:1M-2M', 'Mus musculus')


@pytest.mark.parametrize(
    ('region', 'organism', 'chromosome'),
    [
        ('chr22:1000-2000', 'Homo sapiens', 'chr22'),
        ('chr19:1M-1.1M', 'Mus musculus', 'chr19'),
        ('CHRx:1000-2000', 'Mus musculus', 'chrX'),
        ('y:1000-2000', 'Mus musculus', 'chrY'),
        ('m:1-1000', 'Homo sapiens', 'chrM'),
    ],
)
def test_valid_chromosome_per_organism(region, organism, chromosome):
    """Test that each organism's chromosomes are accepted in any form and case."""
    assert RegionParser.parse_region(region, organism).chromosome == chromosome


def test_unknown_organism():
    """Test that an organism without a chromosome set raises ValueError."""
    with pytest.raises(ValueError, match="Unknown organism: 'Danio rerio'"):
        RegionParser.parse_region('chr1:1000-2000', 'Danio rerio')


def test_invalid_format():
    """Test that invalid formats raise ValueError."""
    with pytest.raises(ValueError, match='Invalid region format'):
        RegionParser.parse_region('chr1-1000-2000')


def test_chromosome_lengths_cover_every_chromosome():
    """Test that every valid chromosome of each organism has a length and an assembly."""
    assert {organism: set(lengths) for organism, lengths in RegionParser.CHROMOSOME_LENGTHS.items()} == (
        RegionParser.VALID_CHROMOSOMES
    )
    assert set(RegionParser.ASSEMBLIES) == set(RegionParser.VALID_CHROMOSOMES)


@pytest.mark.parametrize(
    ('organism', 'chromosome', 'length'),
    [
        ('Homo sapiens', 'chr1', 248_956_422),
        ('Homo sapiens', 'chr21', 46_709_983),
        ('Homo sapiens', 'chrX', 156_040_895),
        ('Homo sapiens', 'chrY', 57_227_415),
        ('Homo sapiens', 'chrM', 16_569),
        ('Mus musculus', 'chr1', 195_154_279),
        ('Mus musculus', 'chr19', 61_420_004),
        ('Mus musculus', 'chrX', 169_476_592),
        ('Mus musculus', 'chrM', 16_299),
    ],
)
def test_chromosome_lengths(organism, chromosome, length):
    """Test chromosome lengths against GRCh38 and GRCm39."""
    assert RegionParser.CHROMOSOME_LENGTHS[organism][chromosome] == length


@pytest.mark.parametrize(
    ('region', 'organism'),
    [
        ('chr1:1-248956422', 'Homo sapiens'),
        ('chr1:248956421-248956422', 'Homo sapiens'),
        ('chrM:1-16569', 'Homo sapiens'),
        ('chrM:0-16569', 'Homo sapiens'),
        ('chr19:1-61420004', 'Mus musculus'),
        ('chrM:1-16299', 'Mus musculus'),
    ],
)
def test_region_up_to_chromosome_end(region, organism):
    """Test that a region ending at the end of the chromosome is not changed."""
    parsed = RegionParser.parse_region(region, organism)
    assert str(parsed) == region
    assert parsed.requested_end is None


@pytest.mark.parametrize(
    ('region', 'organism', 'clipped', 'requested_end'),
    [
        ('chr1:248,900,000-249,000,000', 'Homo sapiens', 'chr1:248900000-248956422', '249,000,000'),
        ('chr1:248956421-248956423', 'Homo sapiens', 'chr1:248956421-248956422', '248956423'),
        ('chrM:1-20000', 'Homo sapiens', 'chrM:1-16569', '20000'),
        ('chr19:1-62000000', 'Mus musculus', 'chr19:1-61420004', '62000000'),
        ('chrM:1-16569', 'Mus musculus', 'chrM:1-16299', '16569'),
        ('chr1:1M-2G', 'Homo sapiens', 'chr1:1000000-248956422', '2G'),
        ('chr2:0-' + '9' * 40, 'Homo sapiens', 'chr2:0-242193529', '9' * 40),
    ],
)
def test_end_beyond_chromosome_end_is_clipped(region, organism, clipped, requested_end):
    """Test that an end beyond the end of the chromosome is clipped to the chromosome length."""
    parsed = RegionParser.parse_region(region, organism)
    assert str(parsed) == clipped
    assert parsed.requested_end == requested_end


@pytest.mark.parametrize(
    ('region', 'organism', 'start', 'end'),
    [
        (
            'chr1:1G-2G',
            'Homo sapiens',
            '1G',
            'chr1 (248,956,422 bp in GRCh38; the largest start position is 248956421)',
        ),
        (
            'chr1:248956422-248956423',
            'Homo sapiens',
            '248956422',
            'chr1 (248,956,422 bp in GRCh38; the largest start position is 248956421)',
        ),
        (
            'chrM:20000-30000',
            'Homo sapiens',
            '20000',
            'chrM (16,569 bp in GRCh38; the largest start position is 16568)',
        ),
        (
            'chr19:62M-63M',
            'Mus musculus',
            '62M',
            'chr19 (61,420,004 bp in GRCm39; the largest start position is 61420003)',
        ),
        (
            'chr1:123456789012345678901234567891-123456789012345678901234567892',
            'Homo sapiens',
            '123456789012345678901234567891',
            'chr1 (248,956,422 bp in GRCh38; the largest start position is 248956421)',
        ),
        ('chr1:' + '9' * 5000 + '-1', 'Homo sapiens', '9' * 5000, 'chr1 (248,956,422 bp in GRCh38;'),
    ],
)
def test_start_beyond_chromosome_end(region, organism, start, end):
    """Test that a start beyond the end of the chromosome raises ValueError."""
    message = rf"^Invalid region: start position '{start}' is beyond the end of {re.escape(end)}"
    with pytest.raises(ValueError, match=message):
        RegionParser.parse_region(region, organism)


def test_start_greater_than_end():
    """Test that start > end raises ValueError."""
    with pytest.raises(ValueError, match='start position.*must be less than end'):
        RegionParser.parse_region('chr1:2000-1000')


def test_negative_position():
    """Test that negative positions raise ValueError."""
    with pytest.raises(ValueError, match='Invalid region format'):
        RegionParser.parse_region('chr1:-1000-2000')


def test_region_str_representation():
    """Test string representation of GenomicRegion."""
    region = GenomicRegion(chromosome='chr1', start=1000, end=2000)
    assert str(region) == 'chr1:1000-2000'


def test_validate_region_size():
    """Test region size validation."""
    region = GenomicRegion(chromosome='chr1', start=0, end=10000)

    # Should not raise for size within limit
    RegionParser.validate_region_size(region, max_size=20000)

    # Should raise for size exceeding limit
    with pytest.raises(ValueError, match='exceeds maximum allowed size'):
        RegionParser.validate_region_size(region, max_size=5000)
