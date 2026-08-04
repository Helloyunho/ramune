from discord.ext import commands
from discord import app_commands, Attachment, File
from utils.cog_logger import CogLogger
from utils.handle_exception import handle_exception
import asyncio
from io import BytesIO


class Crispify(CogLogger):
    @commands.hybrid_command(
        name="crispify",
        description="Make your video/image/audio crispier.",
    )
    @app_commands.describe(
        media="The media file to crispify. Can be an image, video, or audio file.",
    )
    @handle_exception()
    async def crispify_command(self, ctx: commands.Context, media: Attachment):
        self.logger.debug(
            f"Crispify command requested for media: {media.filename}, size: {media.size} bytes"
        )

        if not media:
            await ctx.send("Please provide a media file to crispify.")
            return

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
            cmd = [
                f"ffmpeg",
                "-i",
                media.url,
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
                *(
                    ["-c:v", "png", "-f", "image2pipe"]
                    if target_format == "png"
                    else []
                ),
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
                await ctx.send(
                    f"Failed to crispify the media. FFmpeg error: \n```\n{stderr.decode()}\n```"
                )
                return

        await ctx.send(
            f"Crispified `{media.filename}`",
            file=File(BytesIO(stdout), filename=f"crispified.{target_format}"),
        )


async def setup(bot):
    await bot.add_cog(Crispify(bot))
