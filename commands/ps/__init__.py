from constants import COMMANDS
from discord.ext import commands
from discord import app_commands

PS_COMMANDS = ["changelog"]
COMMANDS.extend([f"ps.{command}" for command in PS_COMMANDS])


class PSGroup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    @commands.hybrid_group(
        name="ps",
        description="Commands related to PlayStation.",
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ps_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send("Please specify a subcommand.")


async def setup(bot):
    await bot.add_cog(PSGroup(bot))
    for command in PS_COMMANDS:
        await bot.load_extension(f"commands.ps.{command}")


async def teardown(bot):
    for command in PS_COMMANDS:
        await bot.unload_extension(f"commands.ps.{command}")
    await bot.remove_cog("PSGroup")
