import aws_cdk as core
import aws_cdk.assertions as assertions

from hello_lambda.hello_lambda_stack import HelloLambdaStack

def test_hello_lambda_stack_resources():
    app = core.App()
    stack = HelloLambdaStack(app, "HelloLambdaStack")
    template = assertions.Template.from_stack(stack)

    urls = [
        "https://www.google.com",
        "https://www.testhaha.com",
        "https://www.wikipedia.org"
    ]

    # -------------------------------
    # 1. Check Monitoring Lambda
    # -------------------------------
    template.has_resource_properties("AWS::Lambda::Function", {
        "Handler": "WHlambda.lambda_handler",
        "Runtime": "python3.12"
    })

    # -------------------------------
    # 2. Check Alarm Logger Lambda
    # -------------------------------
    template.has_resource_properties("AWS::Lambda::Function", {
        "Handler": "alarm_logger.lambda_handler",
        "Runtime": "python3.12"
    })

    # -------------------------------
    # 3. Check DynamoDB table
    # -------------------------------
    template.has_resource_properties("AWS::DynamoDB::Table", {
        "KeySchema": [
            {"AttributeName": "AlarmName", "KeyType": "HASH"},
            {"AttributeName": "Timestamp", "KeyType": "RANGE"}
        ],
        "AttributeDefinitions": [
            {"AttributeName": "AlarmName", "AttributeType": "S"},
            {"AttributeName": "Timestamp", "AttributeType": "S"}
        ]
    })

    # -------------------------------
    # 4. Check SNS Topic
    # -------------------------------
    template.has_resource_properties("AWS::SNS::Topic", {
        "DisplayName": "WebHealth Alarms"
    })

    # -------------------------------
    # 5. Check CloudWatch Alarms for Lambda errors
    # -------------------------------
    template.resource_count_is("AWS::CloudWatch::Alarm", 1 + len(urls)*2)  # 1 lambda error + 2 alarms per URL

    # -------------------------------
    # 6. Check each URL-specific alarms
    # -------------------------------
    for url in urls:
        safe_id = (
            url.replace("https://", "")
            .replace("http://", "")
            .replace(".", "")
            .replace("/", "")
            .replace("-", "")
        )

        # Availability alarm
        template.has_resource_properties("AWS::CloudWatch::Alarm", {
            "AlarmDescription": f"Website {url} is DOWN (Availability < 1)"
        })

        # Latency alarm
        template.has_resource_properties("AWS::CloudWatch::Alarm", {
            "AlarmDescription": f"Website {url} latency is too high (> 2 seconds)"
        })

    # -------------------------------
    # 7. Check EventBridge Rule (5-min schedule)
    # -------------------------------
    template.has_resource_properties("AWS::Events::Rule", {
        "ScheduleExpression": "rate(5 minutes)"
    })