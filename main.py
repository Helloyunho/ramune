import discord
from discord.ext import commands
from dotenv import load_dotenv
from os import getenv
from utils.logger import get_logger
from typing import TYPE_CHECKING
from constants import COMMANDS

if TYPE_CHECKING:
    from logging import Logger

load_dotenv()


class Ramune(commands.Bot):
    logger: "Logger" = get_logger(__name__)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def reload_all_cogs(self):
        for command in COMMANDS:
            if command.count(".") > 0:
                # it's a subcommand, skip it
                continue
            try:
                await self.reload_extension(f"commands.{command}")
                self.logger.info(f"Reloaded command cog: {command}")
            except Exception as e:
                self.logger.error(
                    f"Failed to reload command cog: {command}. Error: {e}"
                )
                raise e

    async def on_ready(self):
        self.logger.info("Ramune is ready!")
        self.logger.info(f"Logged in as {self.user} (ID: {self.user.id})")  # type: ignore
        for command in COMMANDS:
            if command.count(".") > 0:
                # it's a subcommand, skip it
                continue
            await self.load_extension(f"commands.{command}")


client = Ramune("=", intents=discord.Intents.all())
client.run(getenv("DISCORD_API_TOKEN") or "")
