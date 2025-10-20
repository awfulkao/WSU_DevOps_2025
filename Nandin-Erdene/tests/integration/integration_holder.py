import boto3
import json
import pytest

REGION = "ap-southeast-2"
STACK_PREFIX = "Gamma-WebHealthStack"  # or "Beta-WebHealthStack" if testing Beta stage

@pytest.fixture(scope="session")
def lambda_client():
    """Boto3 Lambda client for the chosen region."""
    return boto3.client("lambda", region_name=REGION)


@pytest.fixture(scope="session")
def deployed_lambda_name(lambda_client):
    """Find the Lambda function deployed by CDK dynamically."""
    functions = lambda_client.list_functions()["Functions"]
    for fn in functions:
        if fn["FunctionName"].startswith(STACK_PREFIX):
            return fn["FunctionName"]
    pytest.skip(f"No Lambda found for stack prefix '{STACK_PREFIX}'")


def test_lambda_invocation(lambda_client, deployed_lambda_name):
    """Invoke Lambda and check that it returns expected URL metrics."""
    response = lambda_client.invoke(
        FunctionName=deployed_lambda_name,
        InvocationType="RequestResponse"
    )

    assert response["StatusCode"] == 200

    payload = json.loads(response["Payload"].read())
    assert "statusCode" in payload
    assert payload["statusCode"] == 200
    assert "body" in payload

    body = json.loads(payload["body"])
    assert isinstance(body, list)
    assert len(body) > 0

    for entry in body:
        assert "url" in entry
        assert "available" in entry
        assert "latency_ms" in entry