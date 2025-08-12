from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_iam as iam
)
from constructs import Construct

class HelloLambdaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None: 
        super().__init__(scope, construct_id, **kwargs)

        fn = _lambda.Function(
            self,
            "MyFunction",
            function_name="MyFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="WHlambda.lambda_handler",
            code=_lambda.Code.from_asset("lib/lambda-handler"),
            log_retention = logs.RetentionDays.ONE_DAY,
        )
        fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"]
            )
        )