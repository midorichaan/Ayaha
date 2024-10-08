import discord
from discord.ext import commands

import time

from discord_slash import SlashCommand, SlashContext

class mido_test(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.slash = SlashCommand(bot, sync_commands=True)

    #test slash
    @slash.slash(name="slash")
    async def _slash(self, ctx: SlashContext):
        mt = time.perf_counter()
        m = await ctx.send(content="> 処理中...")

        ws = round(self.bot.latency * 1000, 2)
        ping = round(time.perf_counter() - mt, 3) * 1000
        await m.edit(content=f"> Pong! \nPing: {ping}ms \nWebSocket: {ws}ms")

def setup(bot):
    bot.add_cog(mido_test(bot))
