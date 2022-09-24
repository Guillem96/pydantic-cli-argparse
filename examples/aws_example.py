from pathlib import Path
import pydantic_argparse

aws_app = pydantic_argparse.PydanticCLIApp("aws")
sagemaker_app = pydantic_argparse.PydanticCLIApp("sagemaker")
lambda_app = pydantic_argparse.PydanticCLIApp("lambda")


class AWSArguments(pydantic_argparse.BaseCLIArguments):
    region: str


class SageMakerCreateActionArguments(AWSArguments):
    name: str


class SageMakerCreateArtifactArguments(AWSArguments):
    name: str


class LambdaInvokeArguments(AWSArguments):
    handler_path: Path


class LambdaWaitArguments(AWSArguments):
    name: str


@sagemaker_app.command()
def create_action(args: SageMakerCreateActionArguments) -> None:
    print(args)


@sagemaker_app.command()
def create_artifact(args: SageMakerCreateArtifactArguments) -> None:
    print(args)


@lambda_app.command()
def invoke(args: LambdaInvokeArguments) -> None:
    print(args)


@lambda_app.command()
def wait(args: LambdaWaitArguments) -> None:
    print(args)


aws_app.add_application(sagemaker_app)
aws_app.add_application(lambda_app)

if __name__ == "__main__":
    aws_app()
