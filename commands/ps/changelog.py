from discord.ext import commands
from discord import app_commands
from discord.ext import commands
from utils.cog_logger import CogLogger
from utils.handle_exception import handle_exception
from utils.ps.crawler import fetch_ps4_html, fetch_ps5_html, parse_html


class PsChangeLog(CogLogger):
    @commands.hybrid_command(
        name="changelog",
        description="Sends changelog for latest PlayStation firmware.",
    )
    @app_commands.describe(
        console="The console to get the changelog for. (e.g., ps4, ps5)"
    )
    @app_commands.choices(
        console=[
            app_commands.Choice(name="PlayStation 4", value="ps4"),
            app_commands.Choice(name="PlayStation 5", value="ps5"),
        ]
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @handle_exception()
    async def changelog_command(
        self, ctx: commands.Context, console: str | None = "ps5"
    ):
        self.logger.debug(f"Changelog command requested for console: {console}")
        if console == "ps4":
            ps4_html = await fetch_ps4_html()
            ps4_info = await parse_html(ps4_html)
            await ctx.send(
                f"## Latest PlayStation 4 Version: {ps4_info['version']}\n{ps4_info['details']}"
            )
        elif console == "ps5":
            ps5_html = await fetch_ps5_html()
            ps5_info = await parse_html(ps5_html)
            await ctx.send(
                f"## Latest PlayStation 5 Version: {ps5_info['version']}\n{ps5_info['details']}"
            )
        else:
            await ctx.send(
                "Invalid console. Please choose either 'ps4' or 'ps5'.", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(PsChangeLog(bot))

    ps_group = bot.get_command("ps")
    if ps_group is None:
        bot.logger.error(
            "PS command group not found. Please ensure the PS cog is loaded."
        )
        return

    cmd = bot.get_command("changelog")
    bot.tree.remove_command("changelog")

    if cmd:
        ps_group.add_command(cmd)
