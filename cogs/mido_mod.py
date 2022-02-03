import discord
from discord.ext import commands

from typing import Union

from lib import utils

class mido_mod(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    #check_hierarchy
    def check_hierarchy(self, ctx, user, target):
        return user == ctx.guild.owner or user.top_role > target.top_role

    #check_db
    async def check_db(self):
        try:
            await self.bot.db.execute(
                "SELECT 1"
            )
        except:
            return False
        else:
            return True

    #ban
    @commands.command(name="ban", usage="ban <Member/User> [Reson]")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(self, ctx, target: Union[discord.Member, discord.User, utils.FetchUserConverter]=None, *, reason: str=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")

        if not target:
            return await m.edit(content=f"> {d['punish-member-required']}")

        if target.id == ctx.author.id:
            return await m.edit(content=f"> {d['punish-cannot-self']}")

        if not self.check_hierarchy(ctx, ctx.author, target):
            s = d['punish-cannot-run'].replace("{TYPE}", "Ban")
            return await m.edit(content="> {s}")

        if not reason:
            reason = d["punish-noreason"]

        s = d["pusish-successfully"].replace("{TYPE}", "Ban").replace("{TARGET}", str(target))
        await m.edit(content=f"> {s}")
        await ctx.guild.ban(target, reason=reason)

    #kick
    @commands.command(name="kick", usage="kick <Member> [Reson]")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @commands.guild_only()
    async def kick(self, ctx, target: discord.Member=None, *, reason: str=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")

        if not target:
            return await m.edit(content=f"> {d['punish-member-required']}")

        if target.id == ctx.author.id:
            return await m.edit(content=f"> {d['punish-cannot-self']}")

        if not self.check_hierarchy(ctx, ctx.author, target):
            s = d['punish-cannot-run'].replace("{TYPE}", "Ban")
            return await m.edit(content="> {s}")

        if not reason:
            reason = d["punish-noreason"]

        await ctx.guild.kick(target, reason=reason)

def setup(bot):
    bot.add_cog(mido_mod(bot))
