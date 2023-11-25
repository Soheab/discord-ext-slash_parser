from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional, Union, Generic, Iterator

import discord
from discord import app_commands
from discord.app_commands.transformers import (
    BUILT_IN_TRANSFORMERS as LIBRARY_BUILT_IN_TRANSFORMERS,
)
from discord.ext.commands.converter import _convert_to_bool
from discord.ext import commands

from discord.utils import SequenceProxy

from .errors import (
    NotAString,
    NotAnInteger,
    NotFloat,
    ParsingFailed,
    VariadicArgsFailed,
    InvalidVariadicArguments,
)
from . import utils

if TYPE_CHECKING:
    Interaction = discord.Interaction[Any]

    from _types import ValidConverter, ValueErrors, SuccessConverted, FailedConverted

if TYPE_CHECKING:
    from typing_extensions import TypeVar

    ResultT = TypeVar("ResultT", default=str)
else:
    from typing import TypeVar

    ResultT = TypeVar(
        "ResultT",
    )

__all__ = (
    "BooleanConverter",
    "StringConverter",
    "IntegerConverter",
    "FloatConverter",
    "StringParser",
    "ParseResult",
    "VariadicArgs",
)


class BooleanConverter(app_commands.Transform):
    async def transform(self, interaction: Interaction, argument: str) -> bool:
        return _convert_to_bool(argument)


class StringConverter(app_commands.Transformer):
    async def transform(self, interaction: Interaction, argument: str) -> str:
        try:
            return str(argument)
        except ValueError:
            raise NotAString(argument, self)


class IntegerConverter(app_commands.Transformer):
    async def transform(self, interaction: Interaction, argument: str) -> int:
        try:
            return int(argument)
        except ValueError:
            raise NotAnInteger(argument, self)


class FloatConverter(app_commands.Transform):
    async def transform(self, interaction: Interaction, argument: str) -> float:
        try:
            return float(argument)
        except ValueError:
            raise NotFloat(argument, self)


class _BaseParser(app_commands.Transformer):
    def __init__(
        self,
        *,
        converters: list[ValidConverter] = [str],
        only_values: bool = False,
    ) -> None:
        self.converters: list[ValidConverter] = utils._get_converters(converters)
        self.only_values: bool = only_values

    async def transform(
        self, interaction: Interaction, argument: str
    ) -> Union[dict[str, tuple[ResultT, ValidConverter]], SequenceProxy[ResultT]]:
        converted, used_converter, errors = await utils._run_converters(
            self.converters, interaction, argument
        )
        if not converted:
            raise ParsingFailed(argument, self, errors)

        if self.only_values:
            return SequenceProxy([converted])

        return {argument: (converted, used_converter)}


class ParseResult(Generic[ResultT]):
    """Represents the result of parsing an argument.

    Attributes
    ----------
    argument: :class:`str`
        The full argument that was parsed.
    success: :class:`dict`
        A dict of the values that were successfully converted.
        ``{to_convert: (converted, converter)}``
    failed: :class:`dict`
        A dict of the values that failed to convert.
        ``{to_convert: converter}``
    errors: :class:`dict`
        A dict of the errors that were raised during conversion.
        ``{to_convert: error}``

    Converted values can be accessed via :attr:`converted`.
    """

    def __init__(
        self,
        argument: str,
        success: dict[str, tuple[Any, ValidConverter]],
        failed: dict[str, ValidConverter],
        errors: ValueErrors,
    ) -> None:
        self.argument: str = argument
        self.success: dict[str, tuple[ResultT, ValidConverter]] = success
        self.failed: dict[str, ValidConverter] = failed
        self.errors: ValueErrors = errors

    @property
    def converted(self) -> list[Any]:
        return [value[0] for value in self.success.values()]

    def __iter__(self) -> Iterator[list[Any]]:
        return iter(self.converted)

    def __repr__(self) -> str:
        res = ", ".join(f"{v!r}" for v in self.converted)
        return f"<ParseResult {res}>"


class StringParser(Generic[ResultT], app_commands.Transformer):
    def __init__(
        self,
        *,
        split_by: str = " ",
        converters: list[ValidConverter] = [str],
        only_values: bool = False,
        fail_on_error: bool = False,
    ) -> None:
        self.split_by: str = split_by
        self.converters: Optional[list[ValidConverter]] = utils._get_converters(
            converters
        )
        self.only_values: bool = only_values
        self.fail_on_error: bool = fail_on_error

    @property
    def type(self) -> discord.AppCommandOptionType:
        return discord.AppCommandOptionType.string

    async def transform(
        self, interaction: Interaction, argument: str
    ) -> Union[ParseResult[ResultT], SequenceProxy[ResultT]]:
        success: SuccessConverted = {}
        failed: FailedConverted = {}
        value_errors: ValueErrors = {}

        for value in argument.split(self.split_by):
            converted, converter, error = await utils._run_converters(
                self.converters, interaction, value  # type: ignore
            )
            if converted:
                success[value] = (converted, converter)  # type: ignore
            else:
                failed[value] = converter  # type: ignore

            if error:
                value_errors[value] = error

        if not success or self.fail_on_error and failed:
            raise ParsingFailed(argument, self, value_errors)

        res = ParseResult(argument, success, failed, value_errors)

        if self.only_values:
            return SequenceProxy(res.converted)

        return res  # type: ignore


class VariadicArgs(StringParser[ResultT]):
    def __init__(
        self,
        *,
        min: Optional[int] = None,
        max: Optional[int] = None,
        converters: Union[ValidConverter, list[ValidConverter]] = str,
        split_by: str = " ",
    ) -> None:
        self.min: Optional[int] = min
        self.max: Optional[int] = max
        super().__init__(
            split_by=split_by,
            converters=[converters] if not isinstance(converters, list) else converters,
            only_values=False,
        )

    async def transform(
        self, interaction: Interaction, argument: str
    ) -> SequenceProxy[ResultT]:
        arguments = argument.split(self.split_by)
        res: ParseResult[ResultT]
        try:
            res = await super().transform(interaction, argument)  # type: ignore
        except ParsingFailed as e:
            raise VariadicArgsFailed(argument, arguments, self, e.errors) from e

        if (
            not arguments
            or self.min
            and len(arguments) < self.min
            or self.max
            and len(arguments) > self.max
        ):
            raise InvalidVariadicArguments(argument, arguments, self)

        if not res.success or res.failed or len(res.success) != len(arguments):
            raise VariadicArgsFailed(argument, arguments, self, res.errors)

        return SequenceProxy(res.converted)


BUILT_IN_TRANSFORMERS = {
    discord.Message: commands.MessageConverter,
    discord.Colour: commands.ColourConverter,
    discord.Color: commands.ColourConverter,
    discord.Emoji: commands.EmojiConverter,
    discord.PartialEmoji: commands.PartialEmojiConverter,
    discord.GuildSticker: commands.GuildStickerConverter,
    discord.ScheduledEvent: commands.ScheduledEventConverter,
    discord.Invite: commands.InviteConverter,
    discord.Object: commands.ObjectConverter,
    discord.Game: commands.GameConverter,
    commands.clean_content: LIBRARY_BUILT_IN_TRANSFORMERS[str],
    commands.Range: app_commands.Range,
    bool: BooleanConverter,
} | LIBRARY_BUILT_IN_TRANSFORMERS


APP_COMMAND_TYPE_TO_CONVERTER = {
    discord.AppCommandOptionType.string: StringConverter,
    discord.AppCommandOptionType.integer: IntegerConverter,
    discord.AppCommandOptionType.number: FloatConverter,
    discord.AppCommandOptionType.boolean: BooleanConverter,
    discord.AppCommandOptionType.user: commands.MemberConverter,
    discord.AppCommandOptionType.role: commands.RoleConverter,
    discord.AppCommandOptionType.channel: commands.GuildChannelConverter,
}
