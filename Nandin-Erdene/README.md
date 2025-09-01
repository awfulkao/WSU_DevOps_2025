# Web Health Monitoring with AWS Lambda & CloudWatch

This project monitors the availability and latency of a list of web resources using an AWS Lambda function, publishes custom metrics to CloudWatch, sets up alarms, and visualizes them in a CloudWatch Dashboard.

---

## Table of Contents
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Deployment](#deployment)
- [Usage](#usage)
- [Metrics & Alarms](#metrics--alarms)
- [CloudWatch Dashboard](#cloudwatch-dashboard)

---

## Architecture

1. **AWS Lambda Function** (`WHlambda`)
   - Checks the availability and latency of web URLs.
   - Publishes metrics to CloudWatch.

2. **CloudWatch Metrics**
   - `Availability`: 1 if the site is up, 0 if down.
   - `Latency`: Response time in milliseconds.

3. **CloudWatch Alarms**
   - Lambda runtime errors.
   - Availability drops below 1.
   - Latency exceeds 2000 ms (2 seconds).

4. **CloudWatch Dashboard**
   - Graphs for Availability and Latency per URL.
   - Red horizontal line indicates latency threshold.

---

## Prerequisites

- AWS Account with permissions for:
  - Lambda
  - CloudWatch (Metrics, Alarms, Dashboard)
  - IAM
- AWS CDK installed (v2)
- Python 3.12
- Node.js 18+ for CDK
- Git (for cloning repo)

---

## Deployment

Clone the repository:
   ```bash
   git clone https://github.com/awfulkao/WSU_DevOps_2025.git
   cd WSU_DevOps_2025


Install Dependecies:

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt


Deploy the stack:
    cdk deploy

You can invoke the Lambda with a custom list of URLs via AWS CLI:

aws lambda invoke \
  --function-name MyFunction \
  --payload '{"urls":["https://www.google.com","https://httpbin.org/delay/5"]}' \
  --cli-binary-format raw-in-base64-out \
  response.json

  Metrics & Alarms
Metrics
Metric Name	Description	Namespace
Availability	1 if site is up, 0 if down	KAOPROJECT
Latency	Response time in milliseconds	KAOPROJECT
Alarms

LambdaErrorAlarm: triggers if Lambda runtime errors > 0.

AvailabilityAlarm<site>: triggers if Availability < 1.

LatencyAlarm<site>: triggers if latency > 2000 ms for 2 periods.

CloudWatch Dashboard

Dashboard Name: WebsiteHealthDashboard

Displays:

Availability graph per URL

Latency graph per URL

Red horizontal line at 2000 ms indicating latency threshold

Allows filtering by URL using dashboard variable.