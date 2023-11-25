from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional

import discord
from discord import app_commands

if TYPE_CHECKING:
    from ._types import ValueErrors
    from .converters import VariadicArgs

__all__ = (
    "TransformerError",
    "NotAString",
    "NotAnInteger",
    "NotFloat",
    "ParsingFailed",
    "InvalidVariadicArguments",
    "VariadicArgsFailed",
)


class TransformerError(app_commands.TransformerError):
    """Base exception for all errors raised by this extension."""

    def __init__(
        self,
        value: Any,
        opt_type: discord.AppCommandOptionType,
        transformer: app_commands.Transformer,
        message: Optional[str] = None,
    ) -> None:
        message = message or f"Failed to convert {value} to {transformer._error_display_name!s}"
        app_commands.TransformerError.__init__(self, value, opt_type, transformer)
        app_commands.AppCommandError.__init__(self, message)


class NotAString(TransformerError):
    def __init__(
        self,
        value: Any,
        transformer: app_commands.Transform,
    ) -> None:
        super().__init__(
            value,
            discord.AppCommandOptionType.string,
            transformer,
            f"{value!r} is not a string.",
        )


class NotAnInteger(TransformerError):
    def __init__(
        self,
        value: Any,
        transformer: app_commands.Transform,
    ) -> None:
        super().__init__(
            value,
            discord.AppCommandOptionType.integer,
            transformer,
            f"{value!r} is not an integer.",
        )


class NotFloat(TransformerError):
    def __init__(
        self,
        value: Any,
        transformer: app_commands.Transform,
    ) -> None:
        super().__init__(
            value,
            discord.AppCommandOptionType.integer,
            transformer,
            f"{value!r} is not a decimal number.",
        )


class ParsingFailed(TransformerError):
    def __init__(
        self,
        argument: str,
        transformer: app_commands.Transformer,
        errors: Optional[ValueErrors] = None,
    ) -> None:
        self.errors: Optional[ValueErrors] = errors
        super().__init__(
            argument,
            discord.AppCommandOptionType.string,
            transformer,
            f"Failed to parse {argument!r} to any or all of the converters. Check the errors attribute.",
        )


class InvalidVariadicArguments(TransformerError):
    def __init__(
        self,
        argument: str,
        received_arguments: list[str],
        transformer: VariadicArgs[Any],
    ) -> None:
        what = "Too few"
        if transformer.min and len(received_arguments) < transformer.min:
            what = "Too few"
        elif transformer.max and len(received_arguments) > transformer.max:
            what = "Too many"

        super().__init__(
            argument,
            discord.AppCommandOptionType.string,
            transformer,
            f"{what} arguments. Expected {transformer.min} to {transformer.max} arguments, got {len(received_arguments)}.",
        )
        self.received_arguments: list[str] = received_arguments


class VariadicArgsFailed(InvalidVariadicArguments):
    def __init__(
        self,
        argument: str,
        received_arguments: list[str],
        transformer: VariadicArgs[Any],
        errors: Optional[ValueErrors] = None,
    ) -> None:
        TransformerError.__init__(
            self,  # type: ignore
            argument,
            discord.AppCommandOptionType.string,
            transformer,  # type: ignore
            message=f"{len(errors or [])} arguments failed to be converted. Check the errors attribute.",
        )
        self.received_arguments: list[str] = received_arguments
        self.errors: Optional[ValueErrors] = errors
