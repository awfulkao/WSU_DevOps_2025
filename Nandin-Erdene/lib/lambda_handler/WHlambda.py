#!/usr/bin/env python3
import json
import urllib3
import boto3
import time
import os
import logging

# Metrics names and namespace
URL_MONITOR_AVAILABILITY = "Availability"
URL_MONITOR_LATENCY = "Latency"
URL_NAMESPACE = "KAOPROJECT"

# AWS clients (keep at module-level so tests can monkeypatch)
http = urllib3.PoolManager()
cloudwatch = boto3.client("cloudwatch")

# Get URLs from environment and filter out empty strings
DEFAULT_URLS = [u for u in os.getenv("URLS", "").split(",") if u]

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Monitors the availability and latency of websites,
    pushes metrics to CloudWatch, and logs results.
    """
    # Allow event to override urls (useful for tests)
    urls = event.get("urls", DEFAULT_URLS) if isinstance(event, dict) else DEFAULT_URLS
    results = []

    # If nothing to check, return early (but 200)
    if not urls:
        logger.info("No URLs provided to check.")
        return {"statusCode": 200, "body": json.dumps({"results": [], "message": "no urls configured"})}

    for url in urls:
        # Create a safe ID for CloudWatch alarms or dashboard widgets
        safe_id = url.replace("https://", "").replace("http://", "").replace(".", "").replace("/", "").replace("-", "")

        try:
            # Measure latency
            start_time = time.perf_counter()
            response = http.request("GET", url, timeout=10)
            end_time = time.perf_counter()

            latency_ms = (end_time - start_time) * 1000
            is_available = 200 <= response.status < 300
            availability_value = 1 if is_available else 0

            # Push metrics to CloudWatch (non-fatal if it fails)
            try:
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
            except Exception as cw_err:
                logger.warning("Failed to publish metrics to CloudWatch for %s: %s", url, str(cw_err))

            results.append({
                "url": url,
                "available": is_available,
                "status_code": response.status,
                "latency_ms": latency_ms,
                "metrics_sent": True,
                "safe_id": safe_id
            })

        except Exception as e:
            # If request fails, log and push availability=0 (but ignore CloudWatch errors)
            logger.exception("Error checking URL %s", url)
            try:
                cloudwatch.put_metric_data(
                    Namespace=URL_NAMESPACE,
                    MetricData=[{
                        "MetricName": URL_MONITOR_AVAILABILITY,
                        "Value": 0,
                        "Unit": "Count",
                        "Dimensions": [{"Name": "URL", "Value": url}]
                    }]
                )
            except Exception as cw_err:
                logger.warning("Failed to publish failure metric to CloudWatch for %s: %s", url, str(cw_err))

            results.append({
                "url": url,
                "available": False,
                "error": str(e),
                "metrics_sent": False,
                "safe_id": safe_id
            })

    # Print the results for CloudWatch Logs
    logger.info("Monitoring results: %s", json.dumps(results, indent=2))

    return {
        "statusCode": 200,
        "body": json.dumps(results)
    }
