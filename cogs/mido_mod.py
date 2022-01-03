import discord
from discord.ext import commands

from typing import Union

from lib import utils

class mido_mod(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

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
            return await m.edit(content=f"> {d['member-required']}")

        if target.id == ctx.author.id:
            return await m.edit(content=f"> {d['ban-cannot-self']}")

        if not reason:
            reason = d["ban-noreason"]

        await ctx.guild.ban(target, reason=reason)

def setup(bot):
    bot.add_cog(mido_mod(bot))
