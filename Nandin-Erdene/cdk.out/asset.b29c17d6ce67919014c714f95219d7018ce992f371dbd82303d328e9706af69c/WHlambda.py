import json
import urllib3 
import boto3
import time 

URL_MONITOR_AVAILABILITY = "Availability"
URL_MONITOR_LATENCY = "latency"
URL_NAMESPACE = "KAOPROJECT"

def lambda_handler(event, context):
    client = boto3.client('cloudwatch')
    http = urllib3.PoolManager()

    # Get list of sites from event, or use defaults
    urls = event.get('urls', [
        "https://www.google.com",
        "https://www.amazon.com",
        "https://www.wikipedia.org"
    ])

    results = []  # collect results for all sites

    for url in urls:
        try:
            start_time = time.time()
            response = http.request('GET', url, timeout=10)
            end_time = time.time()

            latency_ms = (end_time - start_time) * 1000
            is_available = 200 <= response.status < 300
            availability_value = 1 if is_available else 0

            # Send metrics for this site
            client.put_metric_data(
                Namespace=URL_NAMESPACE,
                MetricData=[
                    {
                        'MetricName': URL_MONITOR_AVAILABILITY,
                        'Value': availability_value,
                        'Unit': 'Count',
                        'Dimensions': [
                            {"Name": "URL", "Value": url}
                        ]
                    },
                    {
                        'MetricName': URL_MONITOR_LATENCY,
                        'Value': latency_ms,
                        'Unit': 'Milliseconds',
                        'Dimensions': [
                            {"Name": "URL", "Value": url}
                        ]
                    }
                ]
            )

            results.append({
                'url': url,
                'available': is_available,
                'status_code': response.status,
                'latency_ms': latency_ms,
                'metrics_sent': True
            })

        except Exception as e:
            # Log availability = 0 for failed site
            client.put_metric_data(
                Namespace=URL_NAMESPACE,
                MetricData=[
                    {
                        'MetricName': URL_MONITOR_AVAILABILITY,
                        'Value': 0,
                        'Unit': 'Count',
                        'Dimensions': [
                            {"Name": "URL", "Value": url}
                        ]
                    }
                ]
            )

            results.append({
                'url': url,
                'available': False,
                'error': str(e),
                'metrics_sent': True
            })

    # Return all results together
    response = {
        'statusCode': 200,
        'body': json.dumps(results)
    }

    print("Lambda Multi-Site Response:", response)
    return response
