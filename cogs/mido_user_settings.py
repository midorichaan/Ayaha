import discord
from discord.ext import commands

import asyncio
from lib import utils

class mido_user_settings(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        
        self.available_lang = ["ja-jp", "en-us"]
        
    #build_us_embed
    async def build_us_embed(self, ctx, type: int):
        if type == 1:
            e = discord.Embed(title=await self.bot.langutil.get_lang(ctx.author.id, key="usersettings"), 
                              description="",
                              color=self.bot.color,
                              timestamp=ctx.message.created_at
                             )
            e.description = "🇯🇵: ja-jp \n🇺🇸: en-us"
            return e
        else:
            e = discord.Embed(title=await self.bot.langutil.get_lang(ctx.author.id, key="usersettings"), 
                              description="",
                              color=self.bot.color,
                              timestamp=ctx.message.created_at
                             )
        
            settings = ["🏳: {} ({})\n".format(await self.bot.langutil.get_lang(ctx.author.id, key="language"), await self.bot.langutil.get_user_lang(ctx.author.id)),
                        "❌: {}".format(await self.bot.langutil.get_lang(ctx.author.id, key="cancel"))
                       ]
        
            for i in settings:
                e.description += i
        
            return e
    
    #clear_reactions
    async def clear_reactions(self, ctx, msg):
        if ctx.channel.permissions_for(ctx.me).manage_messages:
            await msg.clear_reactions()
        else:
            asyncio.gather(*[msg.remove_reaction(ctx.me, "🏳"), msg.remove_reaction(ctx.me, "❌")])

    #usersettings
    @commands.group(name="usersettings", aliases=["usersetting", "us"], invoke_without_command=True)
    @commands.bot_has_permissions(add_reactions=True, embed_links=True)
    async def usersettings(self, ctx):
        m = await utils.reply_or_send(ctx, content="> {}".format(await self.bot.langutil.get_lang(ctx.author.id, key="loading")))
        await m.edit(content=None, embed=await self.build_us_embed(ctx, 0))
        asyncio.gather(*[m.add_reaction("🏳"), m.add_reaction("❌")])
        
        try:
            r, u = await self.bot.wait_for("reaction_add", check=lambda r, u: u.id == ctx.author.id and r.message.id == m.id, timeout=30.0)
        except asyncio.TimeoutError:
            await self.clear_reactions(ctx, m)
            return await m.edit(content="> {}".format(await self.bot.langutil.get_lang(ctx.author.id, key="timeout")))
        else:
            if r.emoji == "🏳":
                await m.edit(content="> {}".format(await self.bot.langutil.get_lang(ctx.author.id, key="usersetting-select-lang")), 
                             embed=await self.build_us_embed(ctx, 1)
                            )
                
                msg = await self.bot.wait_for("message", check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id and m.content in self.available_lang)
                await self.bot.langutil.set_user_lang(ctx.author.id, lang=msg.content)
                
                await m.edit(content=None, embed=await self.build_us_embed(ctx, 0))
            elif r.emoji == "❌":
                await self.clear_reactions(ctx, m)
        
def setup(bot):
    bot.add_cog(mido_user_settings(bot))
