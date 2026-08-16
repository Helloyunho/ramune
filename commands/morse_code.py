from discord.ext import commands
from discord import app_commands
import discord
import wave
from io import BytesIO
from utils.cog_logger import CogLogger
from utils.handle_exception import handle_exception
from utils.morse_code import text_to_morse, morse_to_audio


class MorseCode(CogLogger):
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
        description="Encodes a given text into Morse code.",
    )
    @app_commands.describe(text="The text to encode into Morse code.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @handle_exception()
    async def encode_command(self, ctx: commands.Context, text: str):
        self.logger.debug(f"Morse encode command requested for text: {text}")
        if not text:
            await ctx.send("Please provide text to encode into Morse code.")
            return

        if not all(char in ".- " for char in text):
            text = text_to_morse(text)

        audio_data = morse_to_audio(text)

        audio_file = BytesIO()
        with wave.open(audio_file, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
            wav_file.writeframes(audio_data)

        audio_file.seek(0)
        await ctx.send(
            content=f"Encoded morse code: `{text}`",
            file=discord.File(audio_file, filename="morse_code.wav"),
        )


async def setup(bot):
    await bot.add_cog(MorseCode(bot))
