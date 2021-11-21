import discord
from discord.ext import commands

class mido_guild_settings(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    
    #build_gs_embed
    async def build_gs_embed(self, ctx, type: int, *, lang: str=None):
        if not lang:
            lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        if type == 0:
            e = discord.Embed(title=d["guildsettings"], 
                              description="",
                              color=self.bot.color,
                              timestamp=ctx.message.created_at
                             )
        
            settings = [
                "❌: {}".format(d["cancel"])
            ]
        
            for i in settings:
                e.description += i
        
            return e
    
    #clear_reactions
    async def clear_reactions(self, ctx, msg):
        if ctx.channel.permissions_for(ctx.me).manage_messages:
            await msg.clear_reactions()
        else:
            asyncio.gather(*[msg.remove_reaction(str(r), ctx.author) for r in msg.reactions()])
    
    #guildsettings
    @commands.command(name="guildsettings", aliases=["guildsetting", "gs", "config"], usage="guildsettings")
    @commands.bot_has_permissions(add_reactions=True, embed_links=True, manage_guilds=True)
    async def guildsettings(self, ctx):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        
        m = await utils.reply_or_send(ctx, content="> {}".format(d["loading"]))
        await m.edit(content=None, embed=await self.build_gs_embed(ctx, 0, lang=lang))
        await m.add_reaction("❌")
        
        while True:
            try:
                r, u = await self.bot.wait_for("reaction_add", check=lambda r, u: u.id == ctx.author.id and r.message.id == m.id, timeout=30.0)
            except asyncio.TimeoutError:
                await self.clear_reactions(ctx, m)
                await m.edit(content="> {}".format(d["timeout"]))
                break
            else:
                if ctx.channel.permissions_for(ctx.me).manage_messages:
                    await m.remove_reaction(str(r), ctx.author)
                
                if r.emoji == "❌":
                    await self.clear_reactions(ctx, m)
                    break

def setup(bot):
    bot.add_cog(mido_guild_settings(bot))
