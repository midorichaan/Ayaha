import discord
from discord.ext import commands

from typing import Union

from lib import utils, times

class mido_mod(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    #check_hierarchy
    def check_hierarchy(self, ctx, user, target):
        return user == ctx.guild.owner or user.top_role > target.top_role

    #timeout_member
    async def timeout_member(self, guild_id: int, target_id: int, *, duration=None, reason: str=None):
        payload = {}
        headers = {
            "Authorization": f"Bot {self.bot.http.token}",
            "User-Agent": "DiscordBot ()",
            "X-Audit-Log-Reason": str(reason)
        }

        if duration:
            payload["communication_disabled_until"] = str(duration)
        else:
            payload["communication_disabled_until"] = None

        async with self.bot.session.request(
            "PATCH",
            f"https://discord.com/api/v9/guilds/{guild_id}/members/{target_id}",
            headers=headers,
            json=payload
        ) as request:
            data = await discord.http.json_or_text(request)
            if request.status != 200:
                raise Exception(f"api returns: {data}")
            else:
                return data

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

    #timeout
    @commands.command(name="timeout", description="メンバーをタイムアウトするよ！", usage="timeout <member> <duration> [reason]")
    @commands.guild_only()
    @commands.has_permissions(kick_members=True, ban_members=True)
    @commands.bot_has_permissions(kick_members=True, ban_members=True)
    async def _timeout(self, ctx, target: discord.Member=None, duration: times.ShortTime=None, *, reason: str=None):
        m = await utils.reply_or_send(ctx, content="> 処理中...")

        if not target:
            return await m.edit(content="> メンバーを指定してね！")

        if not duration:
            return await m.edit(content="> 期間を指定してね！")

        try:
            await self.timeout_member(ctx.guild.id, target.id, duration=duration.dt, reason=reason)
        except Exception as exc:
            return await m.edit(content=f"> エラー \n```py\n{exc}\n```")
        else:
            return await m.edit(content=f"> {target}をタイムアウトしたよ！ ({duration.dt})")

    #untimeout
    @commands.command(name="untimeout", description="メンバーのタイムアウトを解除するよ！", usage="untimeout <member> [reason]")
    @commands.guild_only()
    async def _untimeout(self, ctx, target: discord.Member=None, *, reason: str=None):
        m = await utils.reply_or_send(ctx, content="> 処理中...")

        if not target:
            return await m.edit(content="> メンバーを指定してね！")

        try:
            await self.timeout_member(ctx.guild.id, target.id, duration=None, reason=reason)
        except Exception as exc:
            return await m.edit(content=f"> エラー \n```py\n{exc}\n```")
        else:
            return await m.edit(content=f"> {target}のタイムアウトを解除したよ！")

def setup(bot):
    bot.add_cog(mido_mod(bot))
