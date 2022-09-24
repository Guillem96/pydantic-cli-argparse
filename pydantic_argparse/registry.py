from __future__ import annotations

import argparse
from typing import Any, Callable, Dict, Optional, Type

import pydantic

_AddArgumentHandler = Callable[
    [argparse.ArgumentParser, pydantic.fields.ModelField, str], None
]


def get_type_handler_registry() -> _ArgparseTypeHandlersRegistry:
    return _argparse_type_handler_registry


class _ArgparseTypeHandlersRegistry(object):
    def __init__(self) -> None:
        self._registry: Dict[Type[Any], _AddArgumentHandler] = {}

    def add_handler(
        self, type_: Type[Any], handler_fn: _AddArgumentHandler
    ) -> None:
        if type_ in self._registry:
            raise ValueError(f"{type_} is already registered.")

        self._registry[type_] = handler_fn

    def register(
        self, *types_: Type[Any],
    ) -> Callable[[_AddArgumentHandler], _AddArgumentHandler]:
        def register_dec(
            handler_fn: _AddArgumentHandler,
        ) -> _AddArgumentHandler:
            for type_ in types_:
                self.add_handler(type_, handler_fn)
            return handler_fn

        return register_dec

    def get(
        self, type_: Type[Any], default: Optional[_AddArgumentHandler] = None,
    ) -> _AddArgumentHandler:
        if default is None and type_ not in self._registry:
            raise ValueError(f"{type_} not registered")

        return self._registry.get(type_, default)  # type: ignore


_argparse_type_handler_registry = _ArgparseTypeHandlersRegistry()
