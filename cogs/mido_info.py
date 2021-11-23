import discord
from discord.ext import commands

from lib import utils

class mido_info(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
    
    #profile
    @commands.command(usage="profile [user/member]")
    async def profile(self, ctx, target: utils.FetchUserConverter=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")
        
        if not target:
            target = ctx.author
        
        e = discord.Embed(color=self.bot.color, timestamp=ctx.message.created_at)
        e.set_author(name=f"{target} ({target.id})", icon_url=target.avatar_url_as(static_format="png"))
        e.set_footer(text=f"Requested by {ctx.author} ({ctx.author.id})", icon_url=ctx.author.avatar_url_as(static_format="png"))
        
        db = await self.bot.db.fetchone("SELECT * FROM users WHERE user_id=%s", (target.id,))
        if not db:
            e.add_field(name=d["profile-exists"], value=d["profile-exists-0"])
            e.add_field(name=d["profile-rank"], value=d["profile-rank-0"])
            e.add_field(name=d["profile-verify"], value=d["profile-verify-0"])
            e.add_field(name=d["profile-language"], value="ja-jp")
        else:
            e.add_field(name=d["profile-exists"], value=d["profile-exists-1"])
            e.add_field(name=d["profile-rank"], value=d[f"profile-rank-{db['rank']}"])
            e.add_field(name=d["profile-verify"], value=d[f"profile-verify-{db['verify']}"])
            e.add_field(name=d["profile-language"], value=await self.bot.langutil.get_user_lang(target.id))
            
        return await m.edit(content=None, embed=e)
        
def setup(bot):
    bot.add_cog(mido_info(bot))
