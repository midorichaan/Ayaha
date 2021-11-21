import discord
from discord.ext import commands

class mido_user_settings(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    #usersettings
    @commands.group(name="usersettings", aliases=["usersetting", "us"], invoke_without_command=True)
    async def usersettings(self, ctx):
        lang = await self.bot.langutil.get_lang(ctx.author.id, key="loading")
        m = await utils.reply_or_send(ctx, content=f"> {lang}")
        
        e = discord.Embed(title=await self.bot.langutil.get_lang(ctx.author.id, key="usersetting"), 
                          description="",
                          color=self.bot.color,
                          timestamp=ctx.message.created_at
                         )
        
        settings = ["🏳: {} ({})\n".format(await self.bot.langutil.get_lang(ctx.author.id, key="language"), await self.bot.langutil.get_user_lang(ctx.author.id)),
                    "❌: {}".format(await self.bot.langutil.get_lang(ctx.author.id, key="cancel"))
                   ]
        
        for i in settings:
            e.description += i
        
        await m.edit(content=None. embed=e)
        await m.add_reaction("🏳")
        await m.add_reaction("❌")
        
def setup(bot):
    bot.add_cog(mido_user_settings(bot))
