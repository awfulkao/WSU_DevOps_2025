#!/usr/bin/env python3
import aws_cdk as cdk
from aws_cdk import Environment

# Import the pipeline stack we built
from hello_lambda.pipeline_stack import PipelineStack

# If you still want the option to deploy the app stack standalone
# you can import HelloLambdaStack too:
# from hello_stack import HelloLambdaStack

app = cdk.App()

# Define the environment (your AWS account + region)
env = Environment(
    account="353548851308",
    region="ap-southeast-2"   
)

# Instantiate the pipeline
PipelineStack(app, "WebHealthPipelineStack", env=env)

# (Optional) Deploy HelloLambdaStack directly if needed for local testing
# HelloLambdaStack(app, "WebHealthStandalone", env=env)

app.synth()
