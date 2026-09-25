from discord.ext import commands
from discord import app_commands, Message
import discord
from io import BytesIO
from utils.cog_logger import CogLogger
from utils.handle_exception import handle_exception
from utils.media import Media
from typing import TYPE_CHECKING
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

if TYPE_CHECKING:
    from main import Ramune


class AESCommand(CogLogger):
    def __init__(self, bot: "Ramune"):
        super().__init__(bot)

        param = self.encrypt_command.app_command._params.get("text")  # type: ignore
        if param:
            param.required = True
            param.default = discord.utils.MISSING

        param = self.decrypt_command.app_command._params.get("image")  # type: ignore
        if param:
            param.required = True
            param.default = discord.utils.MISSING

    def encrypt(self, content: str | bytes, key: bytes, iv: bytes) -> bytes:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        if isinstance(content, str):
            content = content.encode("utf-8")
        padded_content = pad(content, AES.block_size)
        encrypted_content = cipher.encrypt(padded_content)
        return encrypted_content

    def decrypt(self, data: bytes, key: bytes, iv: bytes) -> str | bytes | None:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        try:
            decrypted_content = unpad(cipher.decrypt(data), AES.block_size)
            try:
                return decrypted_content.decode("utf-8")
            except UnicodeDecodeError:
                return decrypted_content
        except ValueError:
            self.logger.error("Decryption failed. Invalid padding.")
            return None

    @commands.hybrid_group(
        name="aes",
        description="A group of commands for encrypting and decrypting AES CBC.",
    )
    async def aes_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "Please specify a subcommand. Use `/aes encrypt` or `/aes decrypt`.",
                ephemeral=True,
            )

    @aes_group.command(
        name="encrypt",
        description="Encrypts a given text using AES CBC. Prefix with 0x to indicate hex input.",
    )
    @app_commands.describe(
        key="Key for encryption. It must be 16, 24, or 32 bytes.",
        iv="IV for encryption. It must be 16 bytes.",
        text="The text to encrypt.",
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @handle_exception()
    async def encrypt_command(
        self, ctx: commands.Context, key: str, iv: str, *, text: str | None = None
    ):
        if not text:
            if (
                ctx.message.reference
                and (message_reference := ctx.message.reference.resolved)
                and isinstance(message_reference, Message)
                and message_reference.content
            ):
                text = message_reference.content
            else:
                await ctx.send("Please provide text to encrypt.", ephemeral=True)
                return
        text = text.strip()
        if len(text) == 0:
            await ctx.send("Please provide text to encrypt.", ephemeral=True)
            return

        key_bytes: bytes = (
            bytes.fromhex(key[2:]) if key.startswith("0x") else key.encode("utf-8")
        )
        iv_bytes: bytes = (
            bytes.fromhex(iv[2:]) if iv.startswith("0x") else iv.encode("utf-8")
        )
        if len(key_bytes) not in (16, 24, 32):
            await ctx.send("Key must be 16, 24, or 32 bytes long.", ephemeral=True)
            return
        if len(iv_bytes) != 16:
            await ctx.send("IV must be 16 bytes long.", ephemeral=True)
            return

        self.logger.debug(f"AES CBC text encrypt command requested for text: {text}")
        async with ctx.typing():
            encrypted_data = await self.bot.loop.run_in_executor(
                None, self.encrypt, text.encode("utf-8"), key_bytes, iv_bytes
            )

        if len(encrypted_data) > 900:
            encrypted_io = BytesIO(encrypted_data)
            await ctx.send(
                "Sending as file due to size.",
                file=discord.File(encrypted_io, filename="encrypted.bin"),
            )
        else:
            await ctx.send(f"Encrypted data (hex): `{encrypted_data.hex()}`")

    @aes_group.command(
        name="decrypt",
        description="Decrypts a given text using AES CBC. Prefix with 0x to indicate hex input for key and iv.",
    )
    @app_commands.describe(
        key="Key for decryption. It must be 16, 24, or 32 bytes.",
        iv="IV for decryption. It must be 16 bytes.",
        hex="The hex text to decrypt. Containing non-hex character is not allowed.",
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @handle_exception()
    async def decrypt_command(self, ctx: commands.Context, key: str, iv: str, hex: str):
        if not hex:
            if (
                ctx.message.reference
                and (message_reference := ctx.message.reference.resolved)
                and isinstance(message_reference, Message)
                and message_reference.content
            ):
                hex = message_reference.content
            else:
                await ctx.send("Please provide hex to decrypt.", ephemeral=True)
                return
        hex = hex.strip()
        if len(hex) == 0:
            await ctx.send("Please provide hex to decrypt.", ephemeral=True)
            return

        self.logger.debug(f"AES CBC text decrypt command requested for hex: {hex}")

        key_bytes: bytes = (
            bytes.fromhex(key[2:]) if key.startswith("0x") else key.encode("utf-8")
        )
        iv_bytes: bytes = (
            bytes.fromhex(iv[2:]) if iv.startswith("0x") else iv.encode("utf-8")
        )
        data = bytes.fromhex(hex[2:]) if hex.startswith("0x") else bytes.fromhex(hex)
        if len(key_bytes) not in (16, 24, 32):
            await ctx.send("Key must be 16, 24, or 32 bytes long.", ephemeral=True)
            return
        if len(iv_bytes) != 16:
            await ctx.send("IV must be 16 bytes long.", ephemeral=True)
            return

        async with ctx.typing():
            data = await self.bot.loop.run_in_executor(
                None, self.decrypt, data, key_bytes, iv_bytes
            )

        if data:
            if isinstance(data, bytes):
                await ctx.send(
                    "Decrypted data",
                    file=discord.File(BytesIO(data), filename="decrypted.bin"),
                )
            else:
                await ctx.send(f"Decrypted data: `{data}`")
        else:
            await ctx.send(
                "Failed to decrypt the provided hex. Please check your key, iv, and hex input.",
                ephemeral=True,
            )

    @aes_group.command(
        name="encrypt_file",
        description="Encrypts a given file using AES CBC. Prefix with 0x to indicate hex input.",
    )
    @app_commands.describe(
        key="Key for encryption. It must be 16, 24, or 32 bytes.",
        iv="IV for encryption. It must be 16 bytes.",
        file="The file to encrypt.",
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @handle_exception()
    async def encrypt_file_command(
        self,
        ctx: commands.Context,
        key: str,
        iv: str,
        file: discord.Attachment | None = None,
    ):
        media_converted: Media
        if not file:
            if (
                ctx.message.reference
                and (message_reference := ctx.message.reference.resolved)
                and isinstance(message_reference, Message)
                and message_reference.attachments
            ):
                media_converted = Media(self.bot.http, message_reference.attachments[0])
            elif (
                ctx.message.embeds
                and len(ctx.message.embeds) > 0
                and ctx.message.embeds[0].type in ["image", "video", "gifv"]
            ):
                media_converted = Media(self.bot.http, ctx.message.embeds[0])
            else:
                await ctx.send(
                    "Please provide a media file to encrypt.", ephemeral=True
                )
                return
        else:
            media_converted = Media(self.bot.http, file)

        key_bytes: bytes = (
            bytes.fromhex(key[2:]) if key.startswith("0x") else key.encode("utf-8")
        )
        iv_bytes: bytes = (
            bytes.fromhex(iv[2:]) if iv.startswith("0x") else iv.encode("utf-8")
        )
        if len(key_bytes) not in (16, 24, 32):
            await ctx.send("Key must be 16, 24, or 32 bytes long.", ephemeral=True)
            return
        if len(iv_bytes) != 16:
            await ctx.send("IV must be 16 bytes long.", ephemeral=True)
            return

        self.logger.debug(
            f"AES CBC file encrypt command requested for media: {media_converted.filename}, size: {media_converted.size} bytes"
        )
        async with ctx.typing():
            data = await media_converted.read()
            encrypted_data = await self.bot.loop.run_in_executor(
                None, self.encrypt, data, key_bytes, iv_bytes
            )

        await ctx.send(
            "Encrypted file",
            file=discord.File(BytesIO(encrypted_data), filename="encrypted.bin"),
        )

    @aes_group.command(
        name="decrypt_file",
        description="Decrypts a given file using AES CBC. Prefix with 0x to indicate hex input for key and iv.",
    )
    @app_commands.describe(
        key="Key for decryption. It must be 16, 24, or 32 bytes.",
        iv="IV for decryption. It must be 16 bytes.",
        file="The file to decrypt.",
        output_filename="The filename for the decrypted output. Defaults to 'decrypted.bin'.",
    )
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @handle_exception()
    async def decrypt_file_command(
        self,
        ctx: commands.Context,
        key: str,
        iv: str,
        file: discord.Attachment | None = None,
        output_filename: str = "decrypted.bin",
    ):
        media_converted: Media
        if not file:
            if (
                ctx.message.reference
                and (message_reference := ctx.message.reference.resolved)
                and isinstance(message_reference, Message)
                and message_reference.attachments
            ):
                media_converted = Media(self.bot.http, message_reference.attachments[0])
            elif (
                ctx.message.embeds
                and len(ctx.message.embeds) > 0
                and ctx.message.embeds[0].type in ["image", "video", "gifv"]
            ):
                media_converted = Media(self.bot.http, ctx.message.embeds[0])
            else:
                await ctx.send(
                    "Please provide a media file to encrypt.", ephemeral=True
                )
                return
        else:
            media_converted = Media(self.bot.http, file)

        self.logger.debug(
            f"AES CBC text decrypt command requested for media: {media_converted.filename}, size: {media_converted.size} bytes"
        )

        key_bytes: bytes = (
            bytes.fromhex(key[2:]) if key.startswith("0x") else key.encode("utf-8")
        )
        iv_bytes: bytes = (
            bytes.fromhex(iv[2:]) if iv.startswith("0x") else iv.encode("utf-8")
        )
        if len(key_bytes) not in (16, 24, 32):
            await ctx.send("Key must be 16, 24, or 32 bytes long.", ephemeral=True)
            return
        if len(iv_bytes) != 16:
            await ctx.send("IV must be 16 bytes long.", ephemeral=True)
            return

        async with ctx.typing():
            data = await media_converted.read()
            data = await self.bot.loop.run_in_executor(
                None, self.decrypt, data, key_bytes, iv_bytes
            )

        if data:
            if isinstance(data, bytes):
                await ctx.send(
                    "Decrypted data",
                    file=discord.File(BytesIO(data), filename=output_filename),
                )
            else:
                await ctx.send(f"Decrypted data: `{data}`")
        else:
            await ctx.send(
                "Failed to decrypt the provided hex. Please check your key, iv, and hex input.",
                ephemeral=True,
            )


async def setup(bot):
    await bot.add_cog(AESCommand(bot))
