from __future__ import annotations

import abc
import argparse
import enum
import inspect
from pathlib import Path, PosixPath, PurePath, WindowsPath
import sys
from collections.abc import Sequence as ABCSequence
from functools import reduce
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Type,
    TypeVar,
    get_origin,
)

import pydantic

from .registry import get_type_handler_registry

CT = TypeVar("CT", bound="BaseCLIArguments")
CLICommandFn = Callable[["BaseCLIArguments"], None]

_PREFIX_SEPARATOR = "."


class BaseCLIArguments(abc.ABC, pydantic.BaseModel):
    @classmethod
    def to_parser(
        cls: Type[CT], parser: Optional[argparse.ArgumentParser] = None
    ) -> None:
        parser = parser or argparse.ArgumentParser()
        _add_pydantic_model_to_parser(parser, cls)

    @classmethod
    def from_args(cls: Type[CT], args: argparse.Namespace) -> CT:
        args = vars(args)
        unflattened_args = _unflatten_dict(args, separator=_PREFIX_SEPARATOR)
        return cls.parse_obj(unflattened_args)

    @classmethod
    def parse_cli_args(
        cls: Type[CT],
        argv: Sequence[str],
        parser: Optional[argparse.ArgumentParser] = None,
    ) -> CT:
        parser = parser or argparse.ArgumentParser()
        cls.to_parser(parser)
        return cls.from_args(parser.parse_args(argv))


def run(cmd_fn: CLICommandFn) -> None:
    cmd_fn(fetch_cli_arg_type(cmd_fn).parse_cli_args(sys.argv[1:]))
    sys.exit(0)


def fetch_cli_arg_type(cmd_fn: CLICommandFn) -> None:
    t_hints = list(inspect.signature(cmd_fn).parameters.values())
    if len(t_hints) != 1:
        raise ValueError(
            "Invalid command function. It expects only a single argument of "
            "type BaseCLIArguments."
        )

    if not issubclass(t_hints[0].annotation, BaseCLIArguments):
        raise ValueError(
            "The command argument must be a sub-class off `BaseCLIArguments`."
        )
    return t_hints[0].annotation


def _add_pydantic_model_to_parser(
    parser: argparse.ArgumentParser,
    pm: Type[pydantic.BaseModel],
    prefix: str = "",
) -> None:

    registry = get_type_handler_registry()
    for field in pm.__fields__.values():
        handler_fn = registry.get(field.outer_type_, _add_field_option)
        handler_fn(parser, field, prefix)


def _add_field_option(
    parser: argparse.ArgumentParser,
    pf: pydantic.fields.ModelField,
    prefix: str = "",
) -> None:
    is_container = get_origin(pf.outer_type_) in {list, set, ABCSequence}
    is_primitive = pf.type_ in {str, int, float}
    is_enum = issubclass(pf.type_, enum.Enum)
    is_pydantic_model = issubclass(pf.type_, pydantic.BaseModel)

    if get_origin(pf.outer_type_) != None and not is_container:
        raise TypeError(
            "Only List, Set and Sequence are supported when parsing context from CLI"
            f'Found field "{pf.name}" with type {pf.outer_type_}',
        )

    if is_container and (is_primitive or is_enum):
        _sequence_parser_add_argument(parser, pf, type_=pf.type_, prefix=prefix)
    elif is_container and is_pydantic_model:
        _sequence_parser_add_argument(
            parser,
            pf,
            type_=pf.type_.parse_raw,
            prefix=prefix,
        )
    elif is_enum:
        _enum_parser_add_argument(parser, pf, prefix=prefix)
    elif is_pydantic_model:
        _nested_model_parser_add_argument(parser, pf, prefix=prefix)
    else:
        raise TypeError(
            f'Type "{pf.type_.__name__}" of field '
            f'"{pf.name}" is not supported when parsing a context '
            "with `parse_cli_args` method."
        )


@get_type_handler_registry().register(Path, PurePath, PosixPath, WindowsPath)
def _pathlib_path_add_argument(
    parser: argparse.ArgumentParser,
    pf: pydantic.fields.ModelField,
    prefix: str = "",
    type_: Optional[Callable[[str], Any]] = None,
) -> None:
    def _pathlib_check(path: str) -> Path:
        cast_fn = type_ or pf.type_
        # TODO: Check extra pydantic schema for validating path. E.g is file okay?
        return cast_fn(path)

    is_required = _is_value_undef(pf.field_info.default)
    parser.add_argument(
        f"--{prefix}{_field_name(pf)}",
        help=pf.field_info.description,
        required=is_required,
        default=pf.field_info.default,
        type=_pathlib_check,
    )


@get_type_handler_registry().register(int, float, str)
def _default_parser_add_argument(
    parser: argparse.ArgumentParser,
    pf: pydantic.fields.ModelField,
    prefix: str = "",
    type_: Optional[Callable[[str], Any]] = None,
) -> None:
    is_required = _is_value_undef(pf.field_info.default)

    parser.add_argument(
        f"--{prefix}{_field_name(pf)}",
        help=pf.field_info.description,
        required=is_required,
        default=pf.field_info.default,
        type=type_ or pf.type_,
    )


@get_type_handler_registry().register(bool)
def _bool_parser_add_argument(
    parser: argparse.ArgumentParser,
    pf: pydantic.fields.ModelField,
    prefix: str = "",
) -> None:
    name = f"{prefix}{_field_name(pf)}"
    desc = pf.field_info.description
    def_val = (
        pf.field_info.default
        if isinstance(pf.field_info.default, bool)
        else False
    )

    parser.add_argument(f"--{name}", help=desc, action="store_true")
    parser.add_argument(f"--no-{name}", help=desc, action="store_false")
    parser.set_defaults(**{name: def_val or False})


def _nested_model_parser_add_argument(
    parser: argparse.ArgumentParser,
    pf: pydantic.fields.ModelField,
    prefix: str = "",
) -> None:
    _add_pydantic_model_to_parser(
        parser,
        pf.type_,
        prefix=f"{prefix}{_field_name(pf)}{_PREFIX_SEPARATOR}",
    )


def _sequence_parser_add_argument(
    parser: argparse.ArgumentParser,
    pf: pydantic.fields.ModelField,
    type_: Optional[Callable[[str], Any]] = None,
    prefix: str = "",
) -> None:
    is_required = _is_value_undef(pf.field_info.default)

    parser.add_argument(
        f"--{prefix}{_field_name(pf)}",
        help=pf.field_info.description,
        required=is_required,
        nargs="+",
        type=type_ or (lambda x: x),
        default=pf.field_info.default,
    )


def _enum_parser_add_argument(
    parser: argparse.ArgumentParser,
    pf: pydantic.fields.ModelField,
    prefix: str = "",
) -> None:
    is_required = _is_value_undef(pf.field_info.default)

    parser.add_argument(
        f"--{prefix}{_field_name(pf)}",
        help=pf.field_info.description,
        required=is_required,
        default=pf.field_info.default,
        type=pf.type_,
        choices=list(pf.type_),
    )


def _field_name(pf: pydantic.fields.ModelField) -> str:
    name = pf.alias or pf.name
    return name.replace("_", "-")


def _is_value_undef(field_value: Any) -> bool:
    return field_value == ... or isinstance(
        field_value, pydantic.fields.UndefinedType
    )


def _get_nested_default(d: Dict[str, Any], path: List[str]) -> Dict[str, Any]:
    return reduce(lambda d, k: d.setdefault(k, {}), path, d)


def _set_nested(d: Dict[str, Any], path: List[str], value: Any) -> None:
    _get_nested_default(d, path[:-1])[path[-1]] = value


def _unflatten_dict(
    d: Dict[str, Any], separator: str = _PREFIX_SEPARATOR
) -> Dict[str, Any]:
    output: Dict[str, Any] = {}
    for k, v in d.items():
        path = k.split(separator)
        _set_nested(output, path, v)
    return output
