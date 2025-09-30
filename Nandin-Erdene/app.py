#!/usr/bin/env python3
import aws_cdk as cdk
from aws_cdk import Environment

# Import the pipeline stack we built
from pipeline_stack import PipelineStack

# If you still want the option to deploy the app stack standalone
# you can import HelloLambdaStack too:
# from hello_stack import HelloLambdaStack

app = cdk.App()

# Define the environment (your AWS account + region)
env = Environment(
    account="YOUR_AWS_ACCOUNT_ID",   # e.g. "123456789012"
    region="ap-southeast-2"          # or whatever region you’re using
)

# Instantiate the pipeline
PipelineStack(app, "WebHealthPipelineStack", env=env)

# (Optional) Deploy HelloLambdaStack directly if needed for local testing
# HelloLambdaStack(app, "WebHealthStandalone", env=env)

app.synth()
