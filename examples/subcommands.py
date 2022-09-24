from typing import List

import pydantic_argparse


class EvaluationArguments(pydantic_argparse.BaseCLIArguments):
    metrics: List[str]
    threshold: float = 0.5


class TrainingArguments(pydantic_argparse.BaseCLIArguments):
    learning_rate: float
    batch_size: int = 32
    weight_decay: float = 4e-5


app = pydantic_argparse.PydanticCLIApp()


@app.command()
def train(args: TrainingArguments) -> None:
    print("Training:", args)


@app.command()
def evaluate(args: EvaluationArguments) -> None:
    print("Evaluation:", args)


if __name__ == "__main__":
    app()
