from discord.ext import commands
from discord import app_commands, Attachment, File, Message, Interaction
from utils.cog_logger import CogLogger
from utils.handle_exception import handle_exception
import asyncio
import discord.utils
from io import BytesIO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import Ramune


class Crispify(CogLogger):
    def __init__(self, bot: "Ramune"):
        super().__init__(bot)
        self.crispify_menu = app_commands.ContextMenu(
            name="Crispify This Media",
            callback=self.crispify_context_menu,
            allowed_contexts=app_commands.AppCommandContext(
                guild=True, dm_channel=True, private_channel=True
            ),
        )
        self.bot.tree.add_command(self.crispify_menu)
        param = self.crispify_command.app_command._params.get("media")  # type: ignore
        if param:
            param.required = True
            param.default = discord.utils.MISSING

    async def crispify_media(self, url: str, target_format: str) -> bytes | str:
        size = None
        if target_format in ["mp4", "png"]:
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "csv=s=x:p=0",
                url,
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                self.logger.error(f"FFprobe error: {stderr.decode()}")
                return stderr.decode()
            size = stdout.decode().strip().split("x")
            if len(size) != 2:
                self.logger.error(
                    f"FFprobe error: unexpected output: {stdout.decode()}"
                )
                return f"Unexpected FFprobe output: {stdout.decode()}"
            size = [int(dim) for dim in size]
            self.logger.debug(f"Original media size: {size[0]}x{size[1]}")

        cmd = [
            f"ffmpeg",
            "-i",
            url,
            "-loglevel",
            "error",
            "-b:v",
            "16k",
            "-b:a",
            "16k",
            "-vf",
            "scale=-1:36",
            "-movflags",
            "frag_keyframe+empty_moov",
            "-f",
            target_format if target_format != "png" else "image2",
            *(["-c:v", "png", "-f", "image2pipe"] if target_format == "png" else []),
            "-",
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            self.logger.error(f"FFmpeg error: {stderr.decode()}")
            return stderr.decode()

        if target_format in ["mp4", "png"] and size:
            self.logger.debug(f"Resizing back to {size[0]}x{size[1]}")
            resize_cmd = [
                "ffmpeg",
                "-i",
                "-",
                "-loglevel",
                "error",
                "-vf",
                f"scale={size[0]}:{size[1]}",
                "-f",
                target_format if target_format != "png" else "image2pipe",
                *(
                    ["-c:v", "png", "-f", "image2pipe"]
                    if target_format == "png"
                    else []
                ),
                "-",
            ]
            resize_process = await asyncio.create_subprocess_exec(
                *resize_cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await resize_process.communicate(input=stdout)

            if resize_process.returncode != 0:
                self.logger.error(f"FFmpeg resize error: {stderr.decode()}")
                return stderr.decode()

        return stdout

    @commands.hybrid_command(
        name="crispify",
        description="Make your video/image/audio crispier.",
    )
    @app_commands.describe(
        media="The media file to crispify. Can be an image, video, or audio file.",
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @handle_exception()
    async def crispify_command(
        self, ctx: commands.Context, media: Attachment | None = None
    ):
        if not media:
            if (
                ctx.message.reference
                and (message_reference := ctx.message.reference.resolved)
                and isinstance(message_reference, Message)
                and message_reference.attachments
            ):
                media = message_reference.attachments[0]
            else:
                await ctx.send("Please provide a media file to crispify.")
                return

        self.logger.debug(
            f"Crispify command requested for media: {media.filename}, size: {media.size} bytes"
        )

        media_type = (media.content_type or "unknown").split("/")[0]
        if media_type not in ["image", "video", "audio"]:
            await ctx.send(
                "Invalid media type. Please provide an image, video, or audio file."
            )
            return

        target_format = (
            "mp4"
            if media_type == "video"
            else "png" if media_type == "image" else "mp3"
        )

        async with ctx.typing():
            result = await self.crispify_media(media.url, target_format)

            if isinstance(result, str):
                await ctx.send(
                    f"Failed to crispify the media. FFmpeg error: \n```\n{result}\n```"
                )
                return

        await ctx.send(
            f"Crispified `{media.filename}`",
            file=File(BytesIO(result), filename=f"crispified.{target_format}"),
        )

    @handle_exception()
    async def crispify_context_menu(self, interaction: Interaction, message: Message):
        if not message.attachments:
            await interaction.response.send_message(
                "Please provide a media file to crispify.", ephemeral=True
            )
            return

        media = message.attachments[0]
        self.logger.debug(
            f"Crispify command requested for media: {media.filename}, size: {media.size} bytes"
        )

        media_type = (media.content_type or "unknown").split("/")[0]
        if media_type not in ["image", "video", "audio"]:
            await interaction.response.send_message(
                "Invalid media type. Please provide an image, video, or audio file.",
                ephemeral=True,
            )
            return

        target_format = (
            "mp4"
            if media_type == "video"
            else "png" if media_type == "image" else "mp3"
        )

        await interaction.response.defer()

        result = await self.crispify_media(media.url, target_format)

        if isinstance(result, str):
            await interaction.followup.send(
                f"Failed to crispify the media. FFmpeg error: \n```\n{result}\n```",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            f"Crispified `{media.filename}`",
            file=File(BytesIO(result), filename=f"crispified.{target_format}"),
        )


async def setup(bot):
    await bot.add_cog(Crispify(bot))
