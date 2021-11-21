import discord
from discord.ext import commands

import time

from lib import utils

class mido_bot(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
    
    #ping
    @commands.command()
    async def ping(self, ctx):
        msg_time = time.perf_counter()
        
        lang = await self.bot.langutil.get_lang(ctx.author.id, key="ping-pinging")
        m = await utils.reply_or_send(ctx, content=f"> {lang}")
        
        lang = await self.bot.langutil.get_lang(ctx.author.id, key="ping-pong")
        ws = round(self.bot.latency * 1000, 2)
        ping = round(time.perf_counter() - msg_time, 3) * 1000
        await m.edit(content=f"> {lang} \nPing: {ping} \nWebSocket: {ws}")

def setup(bot):
    bot.add_cog(mido_bot(bot))
