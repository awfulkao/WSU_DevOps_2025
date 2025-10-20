from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_iam as iam,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    custom_resources as cr,
)
from constructs import Construct


class HelloLambdaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # -------------------------------
        # 1. URLs to Monitor
        # -------------------------------
        urls = [
            "https://www.google.com",
            "https://www.testhaha.com",
            "https://www.wikipedia.org"
        ]

        # -------------------------------
        # 2. Monitoring Lambda
        # -------------------------------
        fn = _lambda.Function(
            self,
            "MyFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="WHlambda.lambda_handler",
            code=_lambda.Code.from_asset("lib/lambda_handler"),
            environment={"URLS": ",".join(urls)},
            timeout=Duration.seconds(15)
        )

        # If your CDK version supports log retention directly, you can uncomment below:
        # log_group = logs.LogGroup(
        #     self, "MyFunctionLogGroup",
        #     log_group_name=f"/aws/lambda/{fn.function_name}",
        #     retention=logs.RetentionDays.ONE_DAY
        # )

        fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"]
            )
        )

        # -------------------------------
        # 2a. Schedule Lambda every 5 minutes
        # -------------------------------
        schedule_rule = events.Rule(
            self, "FiveMinuteSchedule",
            schedule=events.Schedule.rate(Duration.minutes(5))
        )
        schedule_rule.add_target(targets.LambdaFunction(fn))

        # -------------------------------
        # 2b. Invoke Lambda once immediately after deployment
        # -------------------------------
        cr.AwsCustomResource(
            self, "InvokeLambdaOnce",
            on_create=cr.AwsSdkCall(
                service="Lambda",
                action="invoke",
                parameters={
                    "FunctionName": fn.function_name,
                    "InvocationType": "Event"  # async call
                },
                physical_resource_id=cr.PhysicalResourceId.of("InvokeOnceResource")
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    actions=["lambda:InvokeFunction"],
                    resources=[fn.function_arn]
                )
            ])
        )

        # -------------------------------
        # 3. CloudWatch Alarms
        # -------------------------------
        error_alarm = cloudwatch.Alarm(
            self, "LambdaErrorAlarm",
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            threshold=1,
            evaluation_periods=1,
            metric=fn.metric_errors()
        )

        availability_alarms = []
        latency_alarms = []

        for url in urls:
            safe_id = (
                url.replace("https://", "")
                .replace("http://", "")
                .replace(".", "")
                .replace("/", "")
                .replace("-", "")
            )

            # Availability metric & alarm
            availability_metric = cloudwatch.Metric(
                namespace="KAOPROJECT",
                metric_name="Availability",
                statistic="Average",
                dimensions_map={"URL": url}
            )

            avail_alarm = cloudwatch.Alarm(
                self, f"AvailabilityAlarm{safe_id}",
                comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
                threshold=1,
                evaluation_periods=1,
                metric=availability_metric,
                alarm_description=f"Website {url} is DOWN (Availability < 1)"
            )
            availability_alarms.append(avail_alarm)

            # Latency metric & alarm
            latency_metric = cloudwatch.Metric(
                namespace="KAOPROJECT",
                metric_name="Latency",
                statistic="Average",
                dimensions_map={"URL": url}
            )

            lat_alarm = cloudwatch.Alarm(
                self, f"LatencyAlarm{safe_id}",
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                threshold=2000,
                evaluation_periods=2,
                metric=latency_metric,
                alarm_description=f"Website {url} latency is too high (> 2 seconds)"
            )
            latency_alarms.append(lat_alarm)

        # -------------------------------
        # 4. SNS Topic
        # -------------------------------
        alarm_topic = sns.Topic(self, "AlarmTopic", display_name="WebHealth Alarms")
        alarm_topic.add_subscription(subs.EmailSubscription("kaonandin@gmail.com"))

        # -------------------------------
        # 5. DynamoDB Table
        # -------------------------------
        alarm_table = dynamodb.Table(
    self, "AlarmLogsTable",
    table_name=f"AlarmLogsTable-{self.stack_name}",
    partition_key=dynamodb.Attribute(name="AlarmName", type=dynamodb.AttributeType.STRING),
    sort_key=dynamodb.Attribute(name="Timestamp", type=dynamodb.AttributeType.STRING)
)


        # -------------------------------
        # 6. Alarm Logger Lambda
        # -------------------------------
        logger_fn = _lambda.Function(
            self,
            "AlarmLoggerFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="alarm_logger.lambda_handler",
            code=_lambda.Code.from_asset("lib/lambda_handler"),
            environment={"TABLE_NAME": alarm_table.table_name},
            timeout=Duration.seconds(10)
        )

        alarm_table.grant_write_data(logger_fn)

        # Subscribe logger Lambda to SNS topic
        alarm_topic.add_subscription(subs.LambdaSubscription(logger_fn))

        # -------------------------------
        # 7. Wire Alarms to SNS
        # -------------------------------
        error_alarm.add_alarm_action(cloudwatch_actions.SnsAction(alarm_topic))
        for alarm in availability_alarms + latency_alarms:
            alarm.add_alarm_action(cloudwatch_actions.SnsAction(alarm_topic))

        # -------------------------------
        # 8. Dashboard
        # -------------------------------
        dashboard = cloudwatch.Dashboard(
            self, "WebsiteHealthDashboard",
            default_interval=Duration.days(7)
        )

        for url in urls:
            availability_metric = cloudwatch.Metric(
                namespace="KAOPROJECT",
                metric_name="Availability",
                statistic="Average",
                dimensions_map={"URL": url}
            )
            latency_metric = cloudwatch.Metric(
                namespace="KAOPROJECT",
                metric_name="Latency",
                statistic="Average",
                dimensions_map={"URL": url}
            )

            dashboard.add_widgets(
                cloudwatch.GraphWidget(
                    title=f"Availability - {url}",
                    left=[availability_metric]
                ),
                cloudwatch.GraphWidget(
                    title=f"Latency - {url}",
                    left=[latency_metric]
                )
            )