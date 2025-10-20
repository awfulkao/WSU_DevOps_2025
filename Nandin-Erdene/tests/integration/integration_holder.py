import boto3
import json
import pytest
import os

# -------------------------
# Environment Variables
# -------------------------
REGION = os.getenv("AWS_REGION", "ap-southeast-2")
LAMBDA_NAME = os.getenv("LAMBDA_NAME", "MyFunction")
DDB_TABLE_NAME = os.getenv(
    "DDB_TABLE_NAME",
    "HelloLambdaStack-AlarmLogsTable7C93252F-F3WMW54C0S80"
)
METRIC_NAMESPACE = os.getenv("METRIC_NAMESPACE", "KAOPROJECT")
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN")  # optional

# -------------------------
# Fixtures
# -------------------------
@pytest.fixture
def lambda_client():
    return boto3.client("lambda", region_name=REGION)

@pytest.fixture
def cloudwatch_client():
    return boto3.client("cloudwatch", region_name=REGION)

@pytest.fixture
def dynamodb_client():
    return boto3.client("dynamodb", region_name=REGION)

@pytest.fixture
def sns_client():
    return boto3.client("sns", region_name=REGION)

# -------------------------
# Lambda tests
# -------------------------
def test_lambda_invocation(lambda_client):
    """Invoke Lambda and check that it returns expected URL metrics."""
    response = lambda_client.invoke(
        FunctionName=LAMBDA_NAME,
        InvocationType="RequestResponse"
    )
    payload = json.loads(response["Payload"].read())
    assert "statusCode" in payload
    assert payload["statusCode"] == 200
    body = json.loads(payload["body"])
    assert isinstance(body, list)
    assert len(body) > 0
    first = body[0]
    for key in ["url", "available", "latency_ms", "metrics_sent", "safe_id"]:
        assert key in first

# -------------------------
# CloudWatch tests
# -------------------------
def test_availability_metric_exists(cloudwatch_client):
    metrics = cloudwatch_client.list_metrics(
        Namespace=METRIC_NAMESPACE, MetricName="Availability"
    )
    assert len(metrics["Metrics"]) > 0

def test_latency_metric_exists(cloudwatch_client):
    metrics = cloudwatch_client.list_metrics(
        Namespace=METRIC_NAMESPACE, MetricName="Latency"
    )
    assert len(metrics["Metrics"]) > 0

# -------------------------
# DynamoDB tests
# -------------------------
def test_table_has_items(dynamodb_client):
    """Ensure DynamoDB table exists and has at least one item."""
    response = dynamodb_client.scan(TableName=DDB_TABLE_NAME, Limit=1)
    assert "Items" in response

# -------------------------
# SNS tests
# -------------------------
def test_sns_topic_exists(sns_client):
    """Check if SNS topic exists (read-only)."""
    if not SNS_TOPIC_ARN:
        pytest.skip("SNS_TOPIC_ARN not provided")
    response = sns_client.list_topics()
    topic_arns = [t["TopicArn"] for t in response["Topics"]]
    assert SNS_TOPIC_ARN in topic_arns
