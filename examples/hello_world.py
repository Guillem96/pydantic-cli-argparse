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