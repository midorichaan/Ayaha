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
    
    #about
    @commands.command(aliases=["info", "bot", "ayaha"])
    async def about(self, ctx):
        lang = await self.bot.langutil.get_lang(ctx.author.id, key="loading")
        m = await utils.reply_or_send(ctx, content=f"> {lang}")
        e = discord.Embed(title=await self.bot.langutil.get_lang(ctx.author.id, key="about-ayaha"), 
                          description=await self.bot.langutil.get_lang(ctx.author.id, key="about-ayaha-description"),
                          color=self.bot.color,
                          timestamp=ctx.message.created_at
                         )
        e.add_field(name=await self.bot.langutil.get_lang(ctx.author.id, key="guilds"), value=str(len(self.bot.guilds)))
        e.add_field(name=await self.bot.langutil.get_lang(ctx.author.id, key="users"), value=str(len(self.bot.users)))
        e.add_field(name=await self.bot.langutil.get_lang(ctx.author.id, key="invites"), 
                    value="https://discord.com/oauth2/authorize?client_id=911139204531122257&scope=bot", 
                    inline=True
                   )
        await m.edit(content=None, embed=e)

def setup(bot):
    bot.add_cog(mido_bot(bot))
