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

def setup(bot):
    bot.add_cog(mido_guild_settings(bot))
