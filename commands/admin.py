from discord.ext import commands
from discord import app_commands
from utils.cog_logger import CogLogger
from utils.handle_exception import handle_exception
from utils.is_me import is_me
from constants import COMMANDS


class Admin(CogLogger):
    @commands.hybrid_command(
        name="sync",
        description="Syncs the bot's commands with Discord.",
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @is_me()
    @handle_exception()
    async def sync_command(self, ctx: commands.Context):
        self.logger.debug("Command sync requested")
        await self.bot.tree.sync()
        await ctx.send("Commands synced.")

    @commands.hybrid_command(name="reload", description="Reloads a command cog.")
    @app_commands.describe(cog="The name of the command cog to reload.")
    @app_commands.choices(
        cog=[app_commands.Choice(name=command, value=command) for command in COMMANDS]
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @is_me()
    @handle_exception()
    async def reload_command(self, ctx: commands.Context, cog: str | None = None):
        self.logger.debug("Command reload requested")
        msg = await ctx.send(
            f"Reloading command cogs: {cog or 'all'}...", ephemeral=True
        )

        if cog:
            try:
                await self.bot.reload_extension(f"commands.{cog}")
                await msg.edit(content=f"Reloaded command cog: {cog}")
                self.logger.info(f"Reloaded command cog: {cog}")
            except Exception as e:
                await msg.edit(
                    content=f"Failed to reload command cog: {cog}. Error: {e}"
                )
                self.logger.error(f"Failed to reload command cog: {cog}. Error: {e}")
        else:
            try:
                await self.bot.reload_all_cogs()
            except Exception as e:
                await msg.edit(content=f"Failed to reload all command cogs. Error: {e}")
                return

            await msg.edit(content="Reloaded all command cogs.")


async def setup(bot):
    await bot.add_cog(Admin(bot))
