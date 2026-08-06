from discord.ext import commands
from discord import app_commands, Attachment, File, Interaction, Message
from utils.cog_logger import CogLogger
from utils.handle_exception import handle_exception
from utils.media import Media
import math
import discord.utils
from io import BytesIO
from pathlib import Path
from PIL import Image
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import Ramune


class Vevo(CogLogger):
    vevo_logo_path = Path(__file__).parent.parent / "assets" / "vevo_logo.png"

    def __init__(self, bot: "Ramune"):
        super().__init__(bot)
        self.vevo_menu = app_commands.ContextMenu(
            name="Vevo This Image",
            callback=self.vevo_context_menu,
            allowed_contexts=app_commands.AppCommandContext(
                guild=True, dm_channel=True, private_channel=True
            ),
        )
        self.bot.tree.add_command(self.vevo_menu)
        param = self.vevo_command.app_command._params.get("image")  # type: ignore
        if param:
            param.required = True
            param.default = discord.utils.MISSING

    def generate_image(self, image: bytes) -> BytesIO:
        original_image = Image.open(BytesIO(image)).convert("RGBA")
        w, h = original_image.width, original_image.height
        width_based_h = math.ceil(w * 9 / 16)
        if width_based_h >= h:
            original_16_9_size = (w, int(width_based_h))
        else:
            height_based_w = math.ceil(h * 16 / 9)
            original_16_9_size = (int(height_based_w), h)

        vevo_logo = Image.open(self.vevo_logo_path).convert("RGBA")

        logo_width = int(
            original_16_9_size[0] * 0.2
        )  # i actually had to download vevo logo and thumbnail to check this lmao
        logo_height = int(vevo_logo.height * (logo_width / vevo_logo.width))
        vevo_logo_resized = vevo_logo.resize(
            (logo_width, logo_height), Image.Resampling.LANCZOS
        )

        position = (
            int(original_16_9_size[0] * 0.02),
            int(original_16_9_size[1] * 0.875),
        )

        watermarked_image = Image.new("RGBA", original_16_9_size, (0, 0, 0, 255))
        watermarked_image.paste(
            original_image,
            (
                (original_16_9_size[0] - original_image.width) // 2,
                (original_16_9_size[1] - original_image.height) // 2,
            ),
        )
        watermarked_image.paste(vevo_logo_resized, position, vevo_logo_resized)

        output_buffer = BytesIO()
        watermarked_image.save(output_buffer, format="PNG")
        output_buffer.seek(0)
        return output_buffer

    @commands.hybrid_command(
        name="vevo",
        description="Add a Vevo watermark to your image. Your image will be resized to 16:9 to fit the aesthetic.",
    )
    @app_commands.describe(
        image="The image file to add a Vevo watermark to.",
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @handle_exception()
    async def vevo_command(
        self, ctx: commands.Context, image: Attachment | None = None
    ):
        image_converted: Media
        if not image:
            if (
                ctx.message.reference
                and (message_reference := ctx.message.reference.resolved)
                and isinstance(message_reference, Message)
                and message_reference.attachments
            ):
                image_converted = Media(self.bot.http, message_reference.attachments[0])
            elif (
                ctx.message.embeds
                and len(ctx.message.embeds) > 0
                and ctx.message.embeds[0].type in ["image", "video", "gifv"]
            ):
                image_converted = Media(self.bot.http, ctx.message.embeds[0])
            else:
                await ctx.send(
                    "Please provide an image file to add a Vevo watermark to."
                )
                return
        else:
            image_converted = Media(self.bot.http, image)

        self.logger.debug(
            f"Vevo command requested for image: {image_converted.filename}, size: {image_converted.size} bytes"
        )

        image_type = (image_converted.content_type or "unknown").split("/")[0]
        if image_type not in ["image"]:
            await ctx.send("Invalid image type. Please provide an image file.")
            return

        async with ctx.typing():
            image_bytes = await image_converted.read()
            output_buffer = await self.bot.loop.run_in_executor(
                None, self.generate_image, image_bytes
            )

            await ctx.send(file=File(fp=output_buffer, filename="vevo.png"))

    @handle_exception()
    async def vevo_context_menu(self, interaction: Interaction, message: Message):
        if not message.attachments:
            await interaction.response.send_message(
                "Please provide an image file to add a Vevo watermark to.",
                ephemeral=True,
            )
            return

        image_converted = Media(self.bot.http, message.attachments[0])
        self.logger.debug(
            f"Vevo command requested for image: {image_converted.filename}, size: {image_converted.size} bytes"
        )

        if not image_converted:
            await interaction.response.send_message(
                "Please provide an image file to add a Vevo watermark to.",
                ephemeral=True,
            )
            return

        image_type = (image_converted.content_type or "unknown").split("/")[0]
        if image_type not in ["image"]:
            await interaction.response.send_message(
                "Invalid image type. Please provide an image file.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(thinking=True)
        image_bytes = await image_converted.read()
        output_buffer = await self.bot.loop.run_in_executor(
            None, self.generate_image, image_bytes
        )

        await interaction.followup.send(
            file=File(fp=output_buffer, filename="vevo.png")
        )


async def setup(bot):
    await bot.add_cog(Vevo(bot))
