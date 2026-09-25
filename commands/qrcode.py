from discord.ext import commands
from discord import app_commands, Message
import discord
from io import BytesIO
from utils.cog_logger import CogLogger
from utils.handle_exception import handle_exception
from typing import TYPE_CHECKING
import qrcode
import cv2
import numpy as np
from utils.media import Media

if TYPE_CHECKING:
    from main import Ramune


class QRCode(CogLogger):
    detector: cv2.QRCodeDetector = cv2.QRCodeDetector()

    def __init__(self, bot: "Ramune"):
        super().__init__(bot)
        self.encode_menu = app_commands.ContextMenu(
            name="Encode to QR Code",
            callback=self.encode_context_menu,
            allowed_contexts=app_commands.AppCommandContext(
                guild=True, dm_channel=True, private_channel=True
            ),
        )
        self.bot.tree.add_command(self.encode_menu)

        param = self.encode_command.app_command._params.get("text")  # type: ignore
        if param:
            param.required = True
            param.default = discord.utils.MISSING

    def generate_qrcode(self, text: str | bytes) -> BytesIO:
        qr = qrcode.QRCode()
        qr.add_data(text, optimize=20 if isinstance(text, str) else 0)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")  # type: ignore
        img_bytes.seek(0)
        return img_bytes

    def decode_qrcode(self, image: bytes) -> str | None:
        img = cv2.imdecode(np.frombuffer(image, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if img is None:
            return None
        data, _, _ = self.detector.detectAndDecode(img)
        return data if data else None

    @commands.hybrid_group(
        name="qrcode",
        description="A group of commands for encoding and decoding QR code.",
    )
    async def qrcode_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "Please specify a subcommand. Use `/qrcode encode` or `/qrcode decode`."
            )

    @qrcode_group.command(
        name="encode",
        description="Encodes a given text into QR code.",
    )
    @app_commands.describe(text="The text to encode into QR code.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @handle_exception()
    async def encode_command(self, ctx: commands.Context, text: str | None = None):
        if not text:
            if (
                ctx.message.reference
                and (message_reference := ctx.message.reference.resolved)
                and isinstance(message_reference, Message)
                and message_reference.content
            ):
                text = message_reference.content
            else:
                await ctx.send("Please provide text to encode into QR code.")
                return
        text = text.strip()
        if len(text) == 0:
            await ctx.send("Please provide text to encode into QR code.")
            return

        self.logger.debug(f"QR code encode command requested for text: {text}")
        async with ctx.typing():
            image = await self.bot.loop.run_in_executor(
                None, self.generate_qrcode, text
            )

        await ctx.send(
            file=discord.File(image, filename="qrcode.png"),
        )

    @handle_exception()
    async def encode_context_menu(
        self, interaction: discord.Interaction, message: Message
    ):
        if not message.content:
            await interaction.response.send_message(
                "Please provide text to encode into QR code.", ephemeral=True
            )
            return
        text = message.content.strip()
        if len(text) == 0:
            await interaction.response.send_message(
                "Please provide text to encode into QR code.", ephemeral=True
            )
            return

        self.logger.debug(f"QR code encode command requested for text: {text}")
        await interaction.response.defer(thinking=True)
        image = await self.bot.loop.run_in_executor(None, self.generate_qrcode, text)

        await interaction.followup.send(
            file=discord.File(image, filename="qrcode.png"),
        )

    @qrcode_group.command(
        name="decode",
        description="Decodes a given text into QR code.",
    )
    @app_commands.describe(image="The image to decode from QR code.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @handle_exception()
    async def decode_command(
        self, ctx: commands.Context, image: discord.Attachment | None = None
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
                await ctx.send("Please provide a media file to decode QR code.")
                return
        else:
            image_converted = Media(self.bot.http, image)

        self.logger.debug(
            f"QR code decode command requested for image: {image_converted.filename}"
        )

        image_type = (image_converted.content_type or "unknown").split("/")[0]
        if image_type not in ["image"]:
            await ctx.send("Invalid image type. Please provide an image file.")
            return

        async with ctx.typing():
            image_bytes = await image_converted.read()
            data = await self.bot.loop.run_in_executor(
                None, self.decode_qrcode, image_bytes
            )

        if data:
            await ctx.send(f"Decoded QR code data: `{data}`")
        else:
            await ctx.send("Failed to decode QR code from the provided image.")

    @handle_exception()
    async def decode_context_menu(
        self, interaction: discord.Interaction, message: Message
    ):
        if not message.attachments:
            await interaction.response.send_message(
                "Please provide an image file to decode QR code.",
                ephemeral=True,
            )
            return

        image_converted = Media(self.bot.http, message.attachments[0])

        self.logger.debug(
            f"QR code decode command requested for image: {image_converted.filename}"
        )

        if not image_converted:
            await interaction.response.send_message(
                "Please provide an image file to add a decode QR code.",
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
        data = await self.bot.loop.run_in_executor(
            None, self.decode_qrcode, image_bytes
        )

        if data:
            await interaction.followup.send(f"Decoded QR code data: `{data}`")
        else:
            await interaction.followup.send(
                "Failed to decode QR code from the provided image."
            )


async def setup(bot):
    await bot.add_cog(QRCode(bot))
