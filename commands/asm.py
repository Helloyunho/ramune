from discord.ext import commands
from discord import app_commands
from utils.cog_logger import CogLogger
from utils.handle_exception import handle_exception
import r2pipe


class Assembly(CogLogger):
    @commands.hybrid_command(
        name="asm",
        description="Assembles a given assembly text. `;`(semicolon) is used as a line separator.",
    )
    @app_commands.describe(
        asm_text="The assembly text to assemble.",
        arch="The architecture to use for assembly.",
        bits="The bit width to use for assembly.",
    )
    @app_commands.choices(
        arch=[
            app_commands.Choice(name="x86", value="x86"),
            app_commands.Choice(name="arm", value="arm"),
            app_commands.Choice(name="mips", value="mips"),
            app_commands.Choice(name="powerpc", value="powerpc"),
        ],
        bits=[
            app_commands.Choice(name="32 Bit", value="32"),
            app_commands.Choice(name="64 Bit", value="64"),
        ],
    )
    @handle_exception()
    async def asm_command(
        self, ctx: commands.Context, asm_text: str, arch: str = "x86", bits: str = "64"
    ):
        self.logger.debug(
            f"Asm command requested for asm text: {asm_text}, arch: {arch}, bits: {bits}"
        )

        if not asm_text:
            await ctx.send("Please provide assembly text to assemble.")
            return
        if arch not in ["x86", "arm", "mips", "powerpc"]:
            await ctx.send(
                "Invalid architecture. Please choose from x86, arm, mips, or powerpc.",
            )
            return
        if bits not in ["32", "64"]:
            await ctx.send("Invalid bit width. Please choose either 32 or 64.")
            return

        await ctx.typing()

        insts = [inst.strip() for inst in asm_text.split(";") if inst.strip()]
        hex_instructions = []

        r2 = r2pipe.open("-")
        r2.cmd(f"e asm.arch={arch}")
        r2.cmd(f"e asm.bits={bits}")

        for inst in insts:
            res = r2.cmd(f"pa {inst}")

            if res and res.strip():
                hex_instructions.append(res.strip())

        assembled_hex = "".join(hex_instructions)
        r2.cmd(f"wx {assembled_hex} @ 0x0") if assembled_hex else None
        disassembled_output = (
            r2.cmd(f"pD {len(assembled_hex.strip()) // 2} @ 0x0")
            if assembled_hex
            else None
        )
        r2.quit()

        if not assembled_hex or assembled_hex.strip() == "" or not disassembled_output:
            await ctx.send(
                "No assembly output generated. Please check the input assembly text."
            )
            return

        await ctx.send(
            f"Hex: `{assembled_hex.strip()}`\nDisassembly:\n```asm\n{disassembled_output}\n```"
        )

    @commands.hybrid_command(
        name="disasm",
        description="Disassembles a given hex text.",
    )
    @app_commands.describe(
        hex_text="The hex text to disassemble.",
        arch="The architecture to use for disassembly.",
        bits="The bit width to use for disassembly.",
    )
    @app_commands.choices(
        arch=[
            app_commands.Choice(name="x86", value="x86"),
            app_commands.Choice(name="arm", value="arm"),
            app_commands.Choice(name="mips", value="mips"),
            app_commands.Choice(name="powerpc", value="powerpc"),
        ],
        bits=[
            app_commands.Choice(name="32 Bit", value="32"),
            app_commands.Choice(name="64 Bit", value="64"),
        ],
    )
    @handle_exception()
    async def disasm_command(
        self, ctx: commands.Context, hex_text: str, arch: str = "x86", bits: str = "64"
    ):
        self.logger.debug(
            f"Disasm command requested for hex text: {hex_text}, arch: {arch}, bits: {bits}"
        )

        if not hex_text:
            await ctx.send("Please provide hex text to disassemble.")
            return
        if arch not in ["x86", "arm", "mips", "powerpc"]:
            await ctx.send(
                "Invalid architecture. Please choose from x86, arm, mips, or powerpc.",
            )
            return
        if bits not in ["32", "64"]:
            await ctx.send("Invalid bit width. Please choose either 32 or 64.")
            return

        await ctx.typing()

        hex_text = "".join(
            [
                c
                for c in hex_text.replace(" ", "").replace("\n", "").replace("0x", "")
                if c in "0123456789abcdefABCDEF"
            ]
        )
        if len(hex_text) % 2 != 0:
            hex_text = hex_text[:-1] + "0" + hex_text[-1]
        hex_len = len(hex_text) // 2

        r2 = r2pipe.open(f"malloc://{hex_len}")
        r2.cmd(f"wx {hex_text} @ 0x0")
        r2.cmd(f"e asm.arch={arch}")
        r2.cmd(f"e asm.bits={bits}")

        disasm_output = r2.cmd(f"pD {hex_len} @ 0x0")
        r2.quit()

        if not disasm_output:
            await ctx.send(
                "No disassembly output generated. Please check the input hex text."
            )
            return

        await ctx.send(f"```asm\n{disasm_output}\n```")


async def setup(bot):
    await bot.add_cog(Assembly(bot))
