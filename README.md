# Pydantic CLI

The simple **yet effective** pydantic CLI argument parser.

Pydantic CLI argument parser is based on the amazing Pydantic and the built-in 
package `argparse`.

## Installation

You can install `pydantic_argparse` with pip:

```
$ pip install git+https://github.com/Guillem96/pydantic-cli.git
```

## How to build your CLI command

*Brewing* 🍺 a CLI command with Pydantic CLI is fairly simple, you only need two 
pour two ingredients: 

- A `pydantic_argparse.BaseCLIArguments` which is subclassing a `pydantic.BaseModel` (so you can define your `pydantic.Field`s as usual). This class will contain all the arguments
that you are expecting the user to provide via CLI.
- An entrypoint: Which is a function that receives an instance of the 
`pydantic_argparse.BaseCLIArguments` class defined.

```python
import pydantic_argparse
import pydantic
import enum

class Style(enum.Enum):
    upper: str = "upper"
    lower: str = "lower"

class SayHelloArguments(pydantic_argparse.BaseCLIArguments):
    name: str = pydantic.Field(..., description="Name to use in hello world msg.")  # required field with help message 
    age: int = 26  # No required field
    style: Style

def main(args: SayHelloArguments) -> None:
    if args.style == Style.upper:
        print(f"Hello, my name is {args.name}. I am {args.age} years old!".upper())
    else:
        print(f"Hello, my name is {args.name}. I am {args.age} years old!".lower())


if __name__ == "__main__":
    pydantic_argparse.run(main)
```

Running the above command with `--help` options shows this message:

```bash
$ python hello_world.py --help
usage: hello_world.py [-h] --name NAME [--age AGE] --style {Style.upper,Style.lower}

optional arguments:
  -h, --help            show this help message and exit
  --name NAME           Name to use in hello world msg.
  --age AGE
  --style {Style.upper,Style.lower}
```

### Sub-commands

You can have a single CLI entrypoint with multiple sub-commands:

```python
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
```

### Multiple CLI applications

For complex projects you may have a lot of commands that (for simplicity) should
be under other commands, organizing them in a tree-like structure. For instance,
Amazon Web Services CLI (`aws`) uses this kind of structure:

```
$ aws sagemaker create-action
$ aws sagemaker create-artifact
...
...
$ aws lambda invoke
$ aws lambda wait
```

You can configure something similar with Pydantic CLI by nesting apps:

```python
# aws.py
import pydantic_argparse
from pathlib import Path

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
    handler: Path

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
```

Check what you've just implemented running these commands:

```bash
$ python aws.py --help
$ python aws.py lambda --help
$ python aws.py sagemaker --help
```

For a more complex example check [Multi apps example](examples/multiple_apps).

### Nested `BaseModel`s

For better code readability organize your CLI arguments in multiple 
`pydantic.BaseModel`s:

```python
import pydantic
import pydantic_argparse

class Person(pydantic.BaseModel):
    name: str
    age: int

class Mock(pydantic.BaseModel):
    count: int
    is_mock: bool
    person: Person

class Arguments(pydantic_argparse.BaseCLIArguments):
    no_nested: int = 10
    mock: Mock

def main(args: Arguments) -> None:
    print(args)

if __name__ == "__main__":
    pydantic_argparse.run(main)
```

```
$ python nested_example.py --help
$ usage: nested_example.py [-h] [--no-nested NO_NESTED] --mock.count MOCK.COUNT [--mock.is-mock] [--no-mock.is-mock]
                        --mock.person.name MOCK.PERSON.NAME --mock.person.age MOCK.PERSON.AGE

optional arguments:
  -h, --help            show this help message and exit
  --no-nested NO_NESTED
  --mock.count MOCK.COUNT
  --mock.is-mock
  --no-mock.is-mock
  --mock.person.name MOCK.PERSON.NAME
  --mock.person.age MOCK.PERSON.AGE
```

#### Sequence of nested models

> ⚠️ Sequence of nested pydantic models is only supported with JSON

```python
class Person(pydantic.BaseModel):
    name: str
    age: int

class  Arguments(pydantic_argparse.BaseCLIArguments):
    people: List[Person]

# has to be provided as follows
# $ python example.py --people '{"name": "a", "age": 1}' '{"name": "a", "age": 2}' '{"name": "a", "age": 3}'
```