from discord.ext import commands
from discord import app_commands, Message
import discord
import wave
from io import BytesIO
from utils.cog_logger import CogLogger
from utils.handle_exception import handle_exception
from utils.morse_code import text_to_morse, morse_to_audio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import Ramune


class MorseCode(CogLogger):
    def __init__(self, bot: "Ramune"):
        super().__init__(bot)
        self.encode_menu = app_commands.ContextMenu(
            name="Encode to Morse Code",
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

    def generate_morse_audio(self, code: str) -> tuple[str, BytesIO]:
        if not all(char in ".- " for char in code):
            code = text_to_morse(code)

        audio_data = morse_to_audio(code)

        audio_file = BytesIO()
        with wave.open(audio_file, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
            wav_file.writeframes(audio_data)

        audio_file.seek(0)
        return code, audio_file

    @commands.hybrid_group(
        name="morse",
        description="A group of commands for encoding and decoding Morse code.",
    )
    async def morse_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "Please specify a subcommand. Use `/morse encode` or `/morse decode`."
            )

    @morse_group.command(
        name="encode",
        description="Encodes a given text into Morse code. if the text is already in Morse code, that code will be converted to audio.",
    )
    @app_commands.describe(text="The text to encode into Morse code.")
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
                await ctx.send("Please provide text to encode into Morse code.")
                return

        self.logger.debug(f"Morse encode command requested for text: {text}")
        code, audio_file = self.generate_morse_audio(text)

        await ctx.send(
            content=f"Encoded morse code: `{code}`",
            file=discord.File(audio_file, filename="morse_code.wav"),
        )

    @handle_exception()
    async def encode_context_menu(
        self, interaction: discord.Interaction, message: Message
    ):
        if not message.content:
            await interaction.response.send_message(
                "Please provide text to encode into Morse code.", ephemeral=True
            )
            return

        self.logger.debug(f"Morse encode command requested for text: {message.content}")
        code, audio_file = self.generate_morse_audio(message.content)

        await interaction.response.send_message(
            content=f"Encoded morse code: `{code}`",
            file=discord.File(audio_file, filename="morse_code.wav"),
        )


async def setup(bot):
    await bot.add_cog(MorseCode(bot))
