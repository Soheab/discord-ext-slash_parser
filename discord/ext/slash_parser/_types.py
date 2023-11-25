from typing import Any, Union

import discord
from discord import app_commands
from discord.ext import commands


ExtCommandsConverter = Union[
    type[commands.ObjectConverter],
    type[commands.MemberConverter],
    type[commands.UserConverter],
    type[commands.MessageConverter],
    type[commands.MessageConverter],
    type[commands.PartialMessageConverter],
    type[commands.TextChannelConverter],
    type[commands.InviteConverter],
    type[commands.GuildConverter],
    type[commands.RoleConverter],
    type[commands.GameConverter],
    type[commands.ColourConverter],
    type[commands.ColorConverter],
    type[commands.VoiceChannelConverter],
    type[commands.StageChannelConverter],
    type[commands.EmojiConverter],
    type[commands.PartialEmojiConverter],
    type[commands.CategoryChannelConverter],
    type[commands.ForumChannelConverter],
    type[commands.ThreadConverter],
    type[commands.GuildChannelConverter],
    type[commands.GuildStickerConverter],
    type[commands.ScheduledEventConverter],
    type[commands.clean_content],
    type[commands.Range],
]
CustomConverter = Union[
    type[app_commands.Transformer],
    type[commands.Converter[Any]],
]
DiscordChannelClasses = Union[
    type[app_commands.AppCommandChannel],
    type[app_commands.AppCommandThread],
    type[discord.abc.GuildChannel],
    type[discord.Thread],
    type[discord.StageChannel],
    type[discord.VoiceChannel],
    type[discord.TextChannel],
    type[discord.CategoryChannel],
    type[discord.ForumChannel],
]
DiscordClass = Union[
    type[discord.User],
    type[discord.Member],
    type[discord.Role],
    # type[discord.Attachment], # not possible to convert
    # ext.commands converters types
    type[discord.Message],
    type[discord.Colour],
    type[discord.Color],
    type[discord.Emoji],
    type[discord.PartialEmoji],
    type[discord.GuildSticker],
    type[discord.ScheduledEvent],
    type[discord.Invite],
    type[discord.Object],
    type[discord.Game],
    DiscordChannelClasses,
]
BuiltinTypes = Union[
    type[str],
    type[int],
    type[float],
    type[bool],
]
ValidConverter = Union[
    DiscordClass,
    ExtCommandsConverter,
    CustomConverter,
]
SuccessConverted = dict[Any, tuple[Any, ValidConverter]]
FailedConverted = dict[Any, ValidConverter]
ValueErrors = dict[Any, Exception]


Interaction = discord.Interaction[Any]
