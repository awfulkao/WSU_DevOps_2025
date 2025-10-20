# tests/test_unit_lambda.py
import time
import json
from lib.lambda_handler import WHlambda

class DummyResp:
    def __init__(self, status, data=b"OK"):
        self.status = status
        self.data = data

def test_lambda_handler_success(monkeypatch):
    # simulate urllib3.PoolManager.request returning 200 quickly
    dummy = DummyResp(200)
    class DummyPool:
        def request(self, method, url, timeout):
            return dummy

    # Avoid real AWS calls during tests
    monkeypatch.setattr(WHlambda, "http", DummyPool())
    monkeypatch.setattr(WHlambda, "cloudwatch", type("C", (), {"put_metric_data": lambda *a, **k: None})())

    event = {"urls": ["https://www.example.com"]}
    result = WHlambda.lambda_handler(event, None)
    assert result["statusCode"] == 200
    body = result["body"]
    assert "example.com" in body or "https://www.example.com" in body or '"url": "https://www.example.com"' in body

def test_lambda_handler_failure(monkeypatch):
    # Simulate exception on request
    class DummyPool:
        def request(self, method, url, timeout):
            raise Exception("connection error")

    monkeypatch.setattr(WHlambda, "http", DummyPool())
    monkeypatch.setattr(WHlambda, "cloudwatch", type("C", (), {"put_metric_data": lambda *a, **k: None})())

    event = {"urls": ["https://doesnotexist.local"]}
    result = WHlambda.lambda_handler(event, None)
    assert result["statusCode"] == 200
    assert '"available": false' in result["body"].lower() or "available" in result["body"]
