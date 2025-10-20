import json
import os
import pytest
import boto3
from unittest.mock import patch, MagicMock

# --- Test Setup ---
@pytest.fixture
def mock_boto3_client(monkeypatch):
    """Mock boto3 CloudWatch client to prevent real AWS calls."""
    mock_client = MagicMock()
    monkeypatch.setattr(boto3, "client", lambda service: mock_client)
    return mock_client


@pytest.fixture
def whlambda_module(mock_boto3_client, monkeypatch):
    """Import the Lambda function module after mocking boto3."""
    monkeypatch.setenv("URLS", "https://www.google.com,https://www.wikipedia.org")
    import importlib
    import sys

    if "lib.lambda_handler.WHlambda" in sys.modules:
        del sys.modules["lib.lambda_handler.WHlambda"]

    import lib.lambda_handler.WHlambda as whlambda
    importlib.reload(whlambda)
    return whlambda


# --- Tests ---
def test_lambda_returns_valid_structure(whlambda_module):
    """Lambda should return a dict with statusCode and body."""
    result = whlambda_module.lambda_handler({}, None)
    assert isinstance(result, dict)
    assert "statusCode" in result
    assert "body" in result
    assert result["statusCode"] == 200


def test_lambda_processes_urls_correctly(whlambda_module):
    """Lambda should return a list of results for each URL."""
    result = whlambda_module.lambda_handler({}, None)
    body = json.loads(result["body"])
    assert isinstance(body, list)
    assert len(body) >= 2

    urls = [entry["url"] for entry in body]
    assert "https://www.google.com" in urls
    assert "https://www.wikipedia.org" in urls


def test_result_fields_are_correct(whlambda_module):
    """Each entry should have expected fields with correct types."""
    result = whlambda_module.lambda_handler({}, None)
    body = json.loads(result["body"])

    for entry in body:
        assert "url" in entry
        assert "available" in entry
        assert isinstance(entry["available"], bool)
        assert "metrics_sent" in entry
        assert isinstance(entry["metrics_sent"], bool)
        assert "safe_id" in entry
        assert isinstance(entry["safe_id"], str)


def test_put_metric_data_called_for_each_url(whlambda_module, mock_boto3_client):
    """Ensure CloudWatch put_metric_data is invoked at least once per URL."""
    result = whlambda_module.lambda_handler({}, None)
    body = json.loads(result["body"])
    call_count = mock_boto3_client.put_metric_data.call_count
    assert call_count >= len(body)