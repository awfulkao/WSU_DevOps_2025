import json
import time
import boto3
import pytest

# -------------------------------
# Configuration
# -------------------------------
REGION = "ap-southeast-2"
LAMBDA_NAME = "MyFunction"  # update if stack appends suffix
DDB_TABLE_PREFIX = "Gamma-WebHealthStack-AlarmLogsTable7C93252F"
SNS_TOPIC_PREFIX = "Gamma-WebHealthStack-AlarmTopic"
EVENT_RULE_NAME = "FiveMinuteSchedule"  # update if necessary
TEST_URLS = ["https://www.google.com", "https://www.wikipedia.org"]

# -------------------------------
# AWS Clients
# -------------------------------
lambda_client = boto3.client("lambda", region_name=REGION)
dynamodb_client = boto3.client("dynamodb", region_name=REGION)
cloudwatch_client = boto3.client("cloudwatch", region_name=REGION)
sns_client = boto3.client("sns", region_name=REGION)
events_client = boto3.client("events", region_name=REGION)

# -------------------------------
# Integration Tests
# -------------------------------
def test_lambda_invocation():
    """Invoke Lambda and check response structure."""
    event = {"urls": TEST_URLS}
    response = lambda_client.invoke(
        FunctionName=LAMBDA_NAME,
        InvocationType="RequestResponse",
        Payload=json.dumps(event)
    )

    payload = json.load(response["Payload"])
    assert payload["statusCode"] == 200

    body = json.loads(payload["body"])
    urls_returned = [entry["url"] for entry in body]
    for url in TEST_URLS:
        assert url in urls_returned
    for entry in body:
        assert "available" in entry
        assert "metrics_sent" in entry
        assert "safe_id" in entry

def test_dynamodb_table_exists_and_logs():
    """Check DynamoDB table exists and optionally has items."""
    tables = dynamodb_client.list_tables()["TableNames"]
    table_name = next((t for t in tables if DDB_TABLE_PREFIX in t), None)
    assert table_name is not None

    # Optional: check table has items
    response = dynamodb_client.scan(TableName=table_name, Limit=1)
    assert "Items" in response

def test_cloudwatch_metrics_exist():
    """Check that CloudWatch metrics for URLs exist."""
    metrics = cloudwatch_client.list_metrics(Namespace="KAOPROJECT")["Metrics"]
    metric_names = {m["MetricName"] for m in metrics}
    assert "Availability" in metric_names
    assert "Latency" in metric_names

    # Check each URL has a metric dimension
    urls_in_metrics = {m["Dimensions"][0]["Value"] for m in metrics if m["MetricName"] in ["Availability", "Latency"]}
    for url in TEST_URLS:
        assert url in urls_in_metrics

def test_sns_topic_exists_and_has_lambda_sub():
    """Check that SNS topic exists and has Lambda subscription."""
    topics = sns_client.list_topics()["Topics"]
    topic_arn = next((t["TopicArn"] for t in topics if SNS_TOPIC_PREFIX in t["TopicArn"]), None)
    assert topic_arn is not None

    subs = sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)["Subscriptions"]
    assert any(sub["Protocol"] == "lambda" for sub in subs)

def test_eventbridge_rule_exists():
    """Check that EventBridge rule exists with correct schedule."""
    rules = events_client.list_rules()["Rules"]
    rule = next((r for r in rules if r["Name"] == EVENT_RULE_NAME), None)
    assert rule is not None
    assert "rate(5 minutes)" in rule.get("ScheduleExpression", "")