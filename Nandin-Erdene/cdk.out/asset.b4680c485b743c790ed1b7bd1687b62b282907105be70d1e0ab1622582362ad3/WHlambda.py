import json
import urllib3
import boto3
import time
import os

URL_MONITOR_AVAILABILITY = "Availability"
URL_MONITOR_LATENCY = "Latency"
URL_NAMESPACE = "KAOPROJECT"

http = urllib3.PoolManager()
client = boto3.client('cloudwatch')

DEFAULT_URLS = os.getenv("URLS", "").split(",")

def lambda_handler(event, context):
    urls = event.get("urls", DEFAULT_URLS)
    results = []
    metric_data = []

    for url in urls:
        try:
            start_time = time.perf_counter()
            response = http.request('GET', url, timeout=10)
            end_time = time.perf_counter()

            latency_ms = (end_time - start_time) * 1000
            is_available = 200 <= response.status < 300
            availability_value = 1 if is_available else 0

        except Exception as e:
            # Failure: mark availability = 0 and latency = 0
            latency_ms = 0
            availability_value = 0
            results.append({
                "url": url,
                "available": False,
                "error": str(e),
                "metrics_sent": True
            })
            # Add metrics for this URL to batch
            metric_data.extend([
                {
                    'MetricName': URL_MONITOR_AVAILABILITY,
                    'Value': availability_value,
                    'Unit': 'Count',
                    'Dimensions': [{'Name': 'URL', 'Value': url}]
                },
                {
                    'MetricName': URL_MONITOR_LATENCY,
                    'Value': latency_ms,
                    'Unit': 'Milliseconds',
                    'Dimensions': [{'Name': 'URL', 'Value': url}]
                }
            ])
            continue  # Skip normal processing for this failed URL

        # Add normal metrics to batch
        metric_data.extend([
            {
                'MetricName': URL_MONITOR_AVAILABILITY,
                'Value': availability_value,
                'Unit': 'Count',
                'Dimensions': [{'Name': 'URL', 'Value': url}]
            },
            {
                'MetricName': URL_MONITOR_LATENCY,
                'Value': latency_ms,
                'Unit': 'Milliseconds',
                'Dimensions': [{'Name': 'URL', 'Value': url}]
            }
        ])

        # Append result for successful URL
        results.append({
            "url": url,
            "available": is_available,
            "status_code": response.status,
            "latency_ms": latency_ms,
            "metrics_sent": True
        })

    # Push all metrics
    if metric_data:
        client.put_metric_data(
            Namespace=URL_NAMESPACE,
            MetricData=metric_data
        )

    return {
        "statusCode": 200,
        "body": json.dumps(results)
    }