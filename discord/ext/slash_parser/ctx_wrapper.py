from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands


class ContextWrapperMessage:
    @property
    def mentions(self):
        return []


if TYPE_CHECKING:

    class ContextWrapper(commands.Context):
        def __init__(self, interaction: discord.Interaction[Any]) -> None:
            ...

else:

    class ContextWrapper:
        __custom_attrs__ = ("bot", "message")

        def __init__(self, interaction: discord.Interaction) -> None:
            self.__original: discord.Interaction = interaction

        def __getattr__(self, name: str) -> Any:
            if name in self.__custom_attrs__:
                return object.__getattribute__(self, name)

            interaction = object.__getattribute__(self, "_ContextWrapper__original")
            return getattr(interaction, name)

        @property
        def bot(self) -> discord.Client:
            return self.__original.client

        @property
        def message(self) -> ContextWrapperMessage:
            return ContextWrapperMessage()
