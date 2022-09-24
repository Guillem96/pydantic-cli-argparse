from typing import List

import pydantic_argparse

app = pydantic_argparse.PydanticCLIApp("sagemaker")


class SageMakerArguments(pydantic_argparse.BaseCLIArguments):
    role: str
    instance_type: str


class EvaluationArguments(SageMakerArguments):
    metrics: List[str]
    threshold: float = 0.5


class TrainingArguments(SageMakerArguments):
    learning_rate: float
    batch_size: int = 32
    weight_decay: float = 4e-5


@app.command()
def train(args: TrainingArguments) -> None:
    print("Training:", args)


@app.command()
def evaluate(args: EvaluationArguments) -> None:
    print("Evaluation:", args)
