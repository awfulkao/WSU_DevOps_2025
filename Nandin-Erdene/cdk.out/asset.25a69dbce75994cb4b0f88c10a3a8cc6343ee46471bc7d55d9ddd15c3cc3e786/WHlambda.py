import json
import urllib3 
import boto3
import time 
URL_MONITOR_AVAILABILITY = "Availability"
URL_MONITOR_LATENCY = "latency"
URL_NAMESPACE = "KAOPROJECT"

def lambda_handler(event,context):

    client = boto3.client('cloudwatch')

    url = event.get('url','https://www.google.com')

    http = urllib3.PoolManager()

    try:
        start_time = time.time()

        response = http.request('GET', url, timeout=10)

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        is_available = 200 <= response.status < 300
        availabilty_value = 1 if is_available else 0

        client.put_metric_data(
            Namespace=URL_NAMESPACE,
            MetricData=[
                {
                    'MetricName': URL_MONITOR_AVAILABILITY,
                    'Value': availabilty_value,
                    'Unit': 'Count'
                },{
                    'MetricName': URL_MONITOR_LATENCY,
                    'Value': latency_ms,
                    'Unit': 'Milliseconds'
                }
            ]
        )

        response =  {
            'statusCode': 200,
            'body': json.dumps({
                'url': url,
                'available': is_available,
                'status_code': response.status,
                'latency_ms': latency_ms,
                'metrics_sent': True
            })
        }

        print("Lambda Response:", response) 
        return response

    except Exception as e:
        client.put_metric_data(
            Namespace=URL_NAMESPACE,
            MetricData=[
                {
                    'MetricName': URL_MONITOR_AVAILABILITY,
                    'Value': 0,
                    'Unit': 'Count'
                }
            ]
        )
        
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'url': url,
                'available': False,
                'error': str(e),
                'metrics_sent': True
            })
        }
        print("Lambda Exception Response:", response)
        return response
