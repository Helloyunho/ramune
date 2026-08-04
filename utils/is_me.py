from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()


def is_me():
    def predicate(ctx: commands.Context):
        owner_id = os.getenv("OWNER_ID")
        if owner_id is None:
            raise ValueError("OWNER_ID is not set in the environment variables.")
        return ctx.author.id == int(owner_id)

    return commands.check(predicate)
