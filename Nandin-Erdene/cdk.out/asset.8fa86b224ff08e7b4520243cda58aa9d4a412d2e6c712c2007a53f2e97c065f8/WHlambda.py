import json
import urllib3
import boto3
import time
import os

# Metrics names and namespace
URL_MONITOR_AVAILABILITY = "Availability"
URL_MONITOR_LATENCY = "Latency"
URL_NAMESPACE = "KAOPROJECT"

# AWS clients
http = urllib3.PoolManager()
cloudwatch = boto3.client("cloudwatch")

# Get URLs from environment
DEFAULT_URLS = os.getenv("URLS", "").split(",")

def lambda_handler(event, context):
    """
    Monitors the availability and latency of websites,
    pushes metrics to CloudWatch.
    """
    urls = event.get("urls", DEFAULT_URLS)
    results = []

    for url in urls:
        safe_id = url.replace("https://", "").replace("http://", "").replace(".", "").replace("/", "").replace("-", "")
        try:
            start_time = time.perf_counter()
            response = http.request("GET", url, timeout=10)
            end_time = time.perf_counter()

            latency_ms = (end_time - start_time) * 1000
            is_available = 200 <= response.status < 300
            availability_value = 1 if is_available else 0

            # Push metrics to CloudWatch
            cloudwatch.put_metric_data(
                Namespace=URL_NAMESPACE,
                MetricData=[
                    {
                        "MetricName": URL_MONITOR_AVAILABILITY,
                        "Value": availability_value,
                        "Unit": "Count",
                        "Dimensions": [{"Name": "URL", "Value": url}]
                    },
                    {
                        "MetricName": URL_MONITOR_LATENCY,
                        "Value": latency_ms,
                        "Unit": "Milliseconds",
                        "Dimensions": [{"Name": "URL", "Value": url}]
                    }
                ]
            )

            results.append({
                "url": url,
                "available": is_available,
                "status_code": response.status,
                "latency_ms": latency_ms,
                "metrics_sent": True
            })

        except Exception as e:
            # In case of failure, availability = 0
            cloudwatch.put_metric_data(
                Namespace=URL_NAMESPACE,
                MetricData=[{
                    "MetricName": URL_MONITOR_AVAILABILITY,
                    "Value": 0,
                    "Unit": "Count",
                    "Dimensions": [{"Name": "URL", "Value": url}]
                }]
            )
            results.append({
                "url": url,
                "available": False,
                "error": str(e),
                "metrics_sent": True
            })

    print("Monitoring results:", json.dumps(results))
    return {"statusCode": 200, "body": json.dumps(results)}