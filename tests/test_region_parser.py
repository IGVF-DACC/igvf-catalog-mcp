"""Tests for region parser."""

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
