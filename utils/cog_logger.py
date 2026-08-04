from discord.ext import commands
from typing import TYPE_CHECKING
from utils.logger import get_logger

if TYPE_CHECKING:
    from logging import Logger
    from main import Ramune


class CogLogger(commands.Cog):
    logger: "Logger"

    def __init__(self, bot: "Ramune"):
        self.bot = bot
        self.logger = get_logger(self.__class__.__name__)
        super().__init__()
