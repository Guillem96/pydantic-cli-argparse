from typing import List

import pydantic_argparse

app = pydantic_argparse.PydanticCLIApp("local")
rf_app = pydantic_argparse.PydanticCLIApp("random-forest")
svm_app = pydantic_argparse.PydanticCLIApp("svm-forest")
app.add_application(rf_app)
app.add_application(svm_app)


class EvaluationArguments(pydantic_argparse.BaseCLIArguments):
    metrics: List[str]
    threshold: float = 0.5


class TrainingArguments(pydantic_argparse.BaseCLIArguments):
    learning_rate: float
    batch_size: int = 32
    weight_decay: float = 4e-5


@rf_app.command()
def train(args: TrainingArguments) -> None:
    print("Random Forest Training:", args)


@svm_app.command()
def train(args: TrainingArguments) -> None:
    print("SVM Training:", args)


@rf_app.command()
def evaluate(args: EvaluationArguments) -> None:
    print("Random Forest Evaluation:", args)


@svm_app.command()
def evaluate(args: EvaluationArguments) -> None:
    print("SVM Evaluation:", args)
