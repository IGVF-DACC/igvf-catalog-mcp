"""Tests for the error formatting."""

import asyncio

import pytest

from igvf_catalog_mcp.services import api_client
from igvf_catalog_mcp.services.formatter import format_error


@pytest.fixture
def client_timeout(monkeypatch):
    monkeypatch.setattr(api_client, '_client', api_client.IGVFCatalogClient(timeout=0.5))


@pytest.mark.parametrize('error', [TimeoutError(), asyncio.TimeoutError()])
def test_format_error_timeout_names_the_timeout(client_timeout, error):
    assert format_error(error) == 'TimeoutError: the IGVF Catalog API did not respond within 0.5 s'


def test_format_error_timeout_with_message_keeps_it(client_timeout):
    assert format_error(TimeoutError('Timeout on reading data from socket')) == (
        'TimeoutError: Timeout on reading data from socket'
    )


def test_format_error_without_message_names_the_type():
    assert format_error(ConnectionResetError()) == 'ConnectionResetError'


def test_format_error_with_message():
    assert format_error(RuntimeError('boom')) == 'RuntimeError: boom'
