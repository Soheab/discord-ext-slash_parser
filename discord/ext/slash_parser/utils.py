from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Type, Union, Any

from inspect import isclass

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from .ctx_wrapper import ContextWrapper

if TYPE_CHECKING:
    from _types import ValidConverter


def _custom_is_subclass(to_check: Union[Type[object], object], classes: Type[object]) -> bool:
    if isclass(to_check):
        return issubclass(to_check, classes)
    else:
        return issubclass(to_check.__class__, classes)


def converter_from_appcommandoptiontype(
    transformer: app_commands.Transformer,
) -> tuple[Union[Type[app_commands.Transformer], Type[commands.Converter]], ...]:
    arg_type = transformer.type
    if arg_type is discord.AppCommandOptionType.attachment:
        raise TypeError("It's not possible to convert attachments via a string. You cannot use this converter.")

    from .converters import (
        StringConverter,
        IntegerConverter,
        FloatConverter,
        BooleanConverter,
    )

    if arg_type is discord.AppCommandOptionType.string:
        return (StringConverter,)
    elif arg_type is discord.AppCommandOptionType.integer:
        return (IntegerConverter,)
    elif arg_type is discord.AppCommandOptionType.number:
        return (FloatConverter,)
    elif arg_type is discord.AppCommandOptionType.boolean:
        return (BooleanConverter,)
    elif arg_type is discord.AppCommandOptionType.user:
        return (commands.MemberConverter,)  # type: ignore
    elif arg_type is discord.AppCommandOptionType.role:
        return (commands.RoleConverter,)  # type: ignore
    elif arg_type is discord.AppCommandOptionType.channel:
        return (commands.GuildChannelConverter,)
    elif arg_type is discord.AppCommandOptionType.mentionable:
        return (
            commands.MemberConverter,
            commands.RoleConverter,
            commands.UserConverter,
        )

    raise TypeError(f"Unknown type {arg_type!r}")


def _unpack_union(
    maybe_union: type,
) -> list[type[object]]:
    if getattr(maybe_union, "__origin__", maybe_union) is Union:
        return list(maybe_union.__args__)  # type: ignore

    return []


def _get_converters(
    converters: list[ValidConverter],
) -> list[ValidConverter]:
    valid_converters = []
    item: ValidConverter
    from .converters import BUILT_IN_TRANSFORMERS, LIBRARY_BUILT_IN_TRANSFORMERS

    for item in converters:
        if union_items := _unpack_union(item):
            # mentionable is a union of Member/User and Role
            if all(
                uitem in (discord.Member, discord.Role) or uitem in (discord.User, discord.Role)
                for uitem in union_items
            ):
                valid_converters.extend(
                    (
                        commands.MemberConverter,
                        commands.RoleConverter,
                        commands.UserConverter,
                    )
                )
            else:
                valid_converters.extend(_get_converters(union_items))
            continue

        if item not in BUILT_IN_TRANSFORMERS:
            if not issubclass(item, (app_commands.Transform, commands.Converter)):  # type: ignore
                raise TypeError(f"Expected a ext.commands.Converter or app_commands.Transform, got {item!r}")
            else:
                valid_converters.append(item)
        elif item in LIBRARY_BUILT_IN_TRANSFORMERS:
            dpy_transformer = LIBRARY_BUILT_IN_TRANSFORMERS[item]
            valid_converters.extend(converter_from_appcommandoptiontype(dpy_transformer))

        else:
            valid_converters.append(BUILT_IN_TRANSFORMERS[item])

    return valid_converters


async def _run_converters(
    converters: list[ValidConverter],
    interaction: Interaction,
    value: str,
) -> tuple[Optional[Any], Optional[ValidConverter], Optional[Exception]]:
    ctx = ContextWrapper(interaction)
    converted_value = None
    used_converter: Optional[ValidConverter] = None

    error: Optional[Exception] = None

    for converter in converters:
        if converted_value:
            break

        used_converter = converter
        instance = converter() if isclass(converter) else converter  # type: ignore

        if _custom_is_subclass(converter, commands.Converter):
            if isclass(converter):
                instance = converter()
            else:
                instance = converter

            try:
                converted_value = await instance.convert(ctx, str(value))  # type: ignore
            except commands.BadArgument as e:
                error = e

        elif _custom_is_subclass(converter, app_commands.Transformer):
            try:
                converted_value = await instance.transform(interaction, value)  # type: ignore
            except app_commands.AppCommandError as e:
                error = e
        else:
            try:
                converted_value = converter(value)  # type: ignore
            except ValueError as e:
                error = e

    return converted_value, used_converter, error
