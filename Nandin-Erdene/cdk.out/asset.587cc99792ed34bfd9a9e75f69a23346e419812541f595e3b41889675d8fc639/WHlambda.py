import json
import urllib3
import boto3
import time
import os

URL_MONITOR_AVAILABILITY = "Availability"
URL_MONITOR_LATENCY = "latency"
URL_NAMESPACE = "KAOPROJECT"

http = urllib3.PoolManager()
client = boto3.client('cloudwatch')


DEFAULT_URLS = os.getenv("URLS", "").split(",")

def lambda_handler(event, context):
    
    urls = event.get("urls", DEFAULT_URLS)

    results = []

    for url in urls:
        try:
            start_time = time.perf_counter()
            response = http.request('GET', url, timeout=10)
            end_time = time.perf_counter()

            latency_ms = (end_time - start_time) * 1000
            is_available = 200 <= response.status < 300
            availability_value = 1 if is_available else 0

            # Push metrics to CloudWatch
            client.put_metric_data(
                Namespace=URL_NAMESPACE,
                MetricData=[
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
            client.put_metric_data(
                Namespace=URL_NAMESPACE,
                MetricData=[{
                    'MetricName': URL_MONITOR_AVAILABILITY,
                    'Value': 0,
                    'Unit': 'Count',
                    'Dimensions': [{'Name': 'URL', 'Value': url}]
                }]
            )
            results.append({
                "url": url,
                "available": False,
                "error": str(e),
                "metrics_sent": True
            })

    return {
        "statusCode": 200,
        "body": json.dumps(results)
    }
