# pipeline_stack.py
from aws_cdk import (
    Stack,
    SecretValue,
    Environment,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    pipelines as pipelines,
)
from constructs import Construct

# Import your application stage / stack
from hello_lambda.hello_lambda_stack import HelloLambdaStack  # adjust import to where your HelloLambdaStack class lives
from aws_cdk import Stage

class WebHealthAppStage(Stage):
    def __init__(self, scope: Construct, id: str, *, env: Environment | None = None):
        super().__init__(scope, id, env=env)
        # Deploy the existing stack as part of the stage
        HelloLambdaStack(self, "WebHealthStack")

class PipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, *, env: Environment | None = None, **kwargs):
        super().__init__(scope, id, env=env, **kwargs)

        # ------------------------
        # 0. GitHub connection details
        # ------------------------
        GITHUB_OWNER = "awfulkao"
        GITHUB_REPO = "WSU_DevOps_2025"
        GITHUB_BRANCH = "main"
        GITHUB_TOKEN_SECRET_NAME = "github-token"

        # ------------------------
        # 1. Source
        # ------------------------
        github_token = SecretValue.secrets_manager(GITHUB_TOKEN_SECRET_NAME)

        source = pipelines.CodePipelineSource.git_hub(
            f"{GITHUB_OWNER}/{GITHUB_REPO}",
            GITHUB_BRANCH,
            authentication=github_token
        )

        # ------------------------
        # 2. Synth step (install deps, synth)
        # ------------------------
        synth = pipelines.ShellStep(
            "Synth",
            input=source,
            commands=[
                # install python env & deps
                "python3 -m pip install --upgrade pip",
                "python3 -m pip install -r Nandin-Erdene/requirements.txt",
                "npm install -g aws-cdk@2.156.0",
                "cd Nandin-Erdene",
                "cdk synth"
            ],
            primary_output_directory="Nandin-Erdene/cdk.out"
        )

        # ------------------------
        # 3. Pipeline
        # ------------------------
        pipeline = pipelines.CodePipeline(self, "WebHealthPipeline",
                                         synth=synth,
                                         cross_account_keys=False,
                                         pipeline_name="WebHealthPipeline")

        # ------------------------
        # 4. Unit tests (pre-synth or pre-deploy)
        #    We'll run unit tests as a separate pre-deploy step for the first non-prod stage.
        # ------------------------
        unit_test_step = pipelines.ShellStep(
            "UnitTests",
            commands=[
                "cd Nandin-Erdene",
                "python3 -m pip install --upgrade pip",
                "python3 -m pip install -r requirements.txt",
                "pytest -q --maxfail=1 --disable-warnings"
            ]
        )

        # ------------------------
        # 5. Add Beta stage with blocking tests
        # ------------------------
        beta_env = env  # deploy to same region account you pass to pipeline stack
        beta_stage = WebHealthAppStage(self, "Beta", env=beta_env)
        pipeline.add_stage(beta_stage, pre=[unit_test_step])

        # ------------------------
        # 6. Add Gamma stage with integration tests (blocker)
        #    Integration tests can be more 'end-to-end' style; they run before the Gamma deploy continues.
        # ------------------------
        integration_test_step = pipelines.ShellStep(
            "IntegrationTests",
            commands=[
                "cd Nandin-Erdene"
                "python3 -m pip install --upgrade pip",
                "python3 -m pip install -r requirements.txt",
                # run any integration tests you place under tests/integration
                "pytest tests/integration -q --maxfail=1 --disable-warnings"
            ]
        )
        gamma_stage = WebHealthAppStage(self, "Gamma", env=beta_env)
        pipeline.add_stage(gamma_stage, pre=[integration_test_step])

        # ------------------------
        # 7. Prod stage - add manual approval (human gate) before production deploy
        # ------------------------
        from aws_cdk.pipelines import ManualApprovalStep
        prod_stage = WebHealthAppStage(self, "Prod", env=beta_env)
        manual_approval = ManualApprovalStep("ManualApprovalBeforeProd",
                                             comment="Approve deploying WebHealth to PROD")
        pipeline.add_stage(prod_stage, pre=[manual_approval])