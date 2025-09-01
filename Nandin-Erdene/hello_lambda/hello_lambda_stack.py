from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_iam as iam,
    aws_cloudwatch as cloudwatch
)
from constructs import Construct

class HelloLambdaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        urls = [
            "https://www.google.com",
            "https://www.amazon.com",
            "https://www.wikipedia.org"
        ]

        fn = _lambda.Function(
            self,
            "MyFunction",
            function_name="MyFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="WHlambda.lambda_handler",
            code=_lambda.Code.from_asset("lib/lambda-handler"),
            environment={
                "URLS": ",".join(urls)
            },
            log_retention=logs.RetentionDays.ONE_DAY,
            timeout=Duration.seconds(15)
        )

        fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"]
            )
        )

        error_alarm = cloudwatch.Alarm(
            self, "LambdaErrorAlarm",
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            threshold=1,
            evaluation_periods=1,
            metric=fn.metric_errors()
        )

        for url in urls:
            availability_metric = cloudwatch.Metric(
                namespace="KAOPROJECT",
                metric_name="Availability",
                statistic="Average",
                dimensions_map={"URL": url}
            )

            cloudwatch.Alarm(
                self, f"AvailabilityAlarm{url.split('//')[1].replace('.', '')}",
                comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
                threshold=1,
                evaluation_periods=1,
                metric=availability_metric,
                alarm_description=f"Website {url} is DOWN (Availability < 1)"
            )

        for url in urls:
            latency_metric = cloudwatch.Metric(
                namespace="KAOPROJECT",
                metric_name="latency",
                statistic="Average",
                dimensions_map={"URL": url}
            )

            cloudwatch.Alarm(
                self, f"LatencyAlarm{url.split('//')[1].replace('.', '')}",
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                threshold=2000,
                evaluation_periods=2,
                metric=latency_metric,
                alarm_description=f"Website {url} latency is too high (> 2 seconds)"
            )

        dashboard = cloudwatch.Dashboard(
            self, "WebsiteHealthDashboard",
            default_interval=Duration.days(7),
            variables=[cloudwatch.DashboardVariable(
                id="url",
                type=cloudwatch.VariableType.PATTERN,
                label="URL",
                input_type=cloudwatch.VariableInputType.INPUT,
                value=".*",
                default_value=cloudwatch.DefaultValue.value(".*"),
                visible=True
            )]
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
                metric_name="latency",
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
                    left=[latency_metric],
                    left_annotations=[
                        cloudwatch.HorizontalAnnotation(
                            value=2000,
                            label="Alarm Threshold (2000 ms)",
                            color="red"
                        )
                    ]
                )
            )