import enum
from typing import Optional, Sequence

import pydantic

import pydantic_argparse


class Mode(enum.Enum):
    FAST: str = "fast"
    SLOW: str = "slow"

    def __str__(self) -> str:
        return self.value


class Person(pydantic.BaseModel):
    name: str
    age: int


class Mock(pydantic.BaseModel):
    count: int
    is_mock: bool
    person: Person


class SupervisedExecutionContext(pydantic_argparse.BaseCLIArguments):
    role: str = pydantic.Field(..., description="testing cli context")
    region: Optional[str] = None
    dry_run: bool
    mode: Mode
    rate: float = 0.8
    prefixes: Sequence[str] = []
    single_count: Mock


def main(args: SupervisedExecutionContext) -> None:
    print(args)


if __name__ == "__main__":
    pydantic_argparse.run(main)
