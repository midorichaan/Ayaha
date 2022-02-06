import discord
from discord.ext import commands

from lib import utils

class mido_info(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    #check_db
    async def check_db(self):
        try:
            await self.bot.db.execute(
                "SELECT 1"
            )
        except:
            return False
        return True

    #shadowban
    @commands.command(aliases=["sb"], usage="shadowban <twitter_id>")
    async def shadowban(self, ctx, twitter_id=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")

        if not twitter_id:
            return await m.edit(content=f"> {d['twitter-id-required']}")

        try:
            async with self.bot.session.request("GET", f"https://shadowban.hmpf.club/{twitter_id}") as r:
                if r.status != 200:
                    return await m.edit(content=f"> {d['exc-cant_fetch-data']}")

                e = discord.Embed(title=f"Shadowban Status ({twitter_id})", description="", color=self.bot.color, timestamp=ctx.message.created_at)
                predicate = lambda i: "✅ " if i else "❌ "
                data = await r.json()
                profile = data["profile"]

                if not profile["exists"] or profile.get["error"]:
                    if not profile.get("protected", None):
                        e.description += f"\n❌ Account Exists"

                        if profile.get("suspended", False):
                            e.description += f"\n❌ Account Suspended"
                        return await m.edit(content=None, embed=e)

                if profile.get("suspended", False):
                    e.description += f"{predicate(profile.get('suspended', False))}"

                banned = data.get("tests", None)
                if not banned:
                    e.description += f"\n✅ Account Exists \n{predicate(not profile.get('protected', False))}Account Protected"
                    return await m.edit(content=None, embed=e)

                dates = [
                    f"\n{predicate(profile['exists'])}Account Exists\n", f"{predicate(profile.get('protected', False))}Account Protected\n",
                    f"{predicate(not banned['ghost']['ban'])}Ghost Ban\n", f"{predicate(banned['search'])}Search Ban\n",
                    f"{predicate(banned['typeahead'])}SearchSuggest Ban\n", f"{predicate(not banned['more_replies'].get('ban', False))}Reply Deboosting\n"
                ]
                for i in dates:
                    e.description += i

                return await m.edit(content=None, embed=e)
        except Exception as exc:
            return await m.edit(content=f"> {d['error']} \n```py\n{exc}\n```")

    #profile
    @commands.command(usage="profile [user/member]")
    async def profile(self, ctx, target: utils.FetchUserConverter=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")

        if not target:
            target = ctx.author

        dbchecker = await self.check_db()
        if not dbchecker:
            return await m.edit(content=f"> {d['exc-cant_fetch-data']}")

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

    #guildinfo
    @commands.command(
        name="guildinfo",
        aliases=[
            "guild", "serverinfo", "si", "server"
        ],
        usage="guildinfo [guild_id]"
    )
    async def guildinfo(self, ctx, target: utils.GuildConverter=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")

        if not target:
            if ctx.guild:
                target = ctx.guild
            else:
                return await m.edit(content=f"> {d['exc-nodm']}")

        dbchecker = await self.check_db()
        if not dbchecker:
            return await m.edit(content=f"> {d['exc-cant_fetch-data']}")

        totalmembers = sum(i for i in target.members)
        botmembers = sum(i for i in target.members if i.bot)

        e = discord.Embed(
            title=f"{target} ({target.id})",
            color=self.bot.color,
            timestamp=ctx.message.created_at
        )
        e.set_thumbnail(url=target.icon_url_as(static_format="png"))
        e.add_field(name=d["guildinfo-name"], value=target.name)
        e.add_field(name=d["guildinfo-id"], value=str(target.id))
        e.add_field(name=d["guildinfo-created_at"], value=target.created_at.strftime("%Y/%m/%d %H:%M:%S"))
        e.add_field(name=d["guildinfo-owner"], value=f"{target.owner} ({target.owner.id})")
        e.add_field(name=d["guildinfo-members"], value=f"")

        return await m.edit(content=None, embed=e)

    #userinfo
    @commands.command(name="userinfo", aliases=["user", "ui"], usage="userinfo [Member/User]")
    async def userinfo(self, ctx, target: utils.FetchUserConverter=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")

        if not target:
            target = ctx.author

        dbchecker = await self.check_db()
        if not dbchecker:
            return await m.edit(content=f"> {d['exc-cant_fetch-data']}")

        is_member = isinstance(target, discord.Member)
        userdb = await self.bot.db.fetchone("SELECT * FROM users WHERE user_id=%s", (target.id,))
        if not userdb:
            await self.bot.db.register_user(target.id, lang="ja-jp")
            userdb = await self.bot.db.fetchone("SELECT * FROM users WHERE user_id=%s", (target.id,))

        e = discord.Embed(
            title=f"{target} ({target.id})",
            color=self.bot.color,
            timestamp=ctx.message.created_at
        )
        e.set_thumbnail(url=target.avatar_url_as(static_format="png"))
        e.add_field(name=d["userinfo-username"], value=f"{target}")
        e.add_field(name=d["userinfo-id"], value=str(target.id))
        e.add_field(name=d["userinfo-created_at"], value=target.created_at.strftime('%Y/%m/%d %H:%M:%S'))

        if is_member:
            e.add_field(name=d["userinfo-joined_at"], value=target.joined_at.strftime('%Y/%m/%d %H:%M:%S'))
            e.add_field(name=d["userinfo-nickname"], value=target.nick or target.name)
            e.add_field(name=d["userinfo-status"], value=utils.get_status(target, db=d))
            e.add_field(
                name=f"{d['userinfo-public_flags']} ({target.public_flags.value})",
                value=utils.get_public_flags(ctx, target)
            )
            e.add_field(name=d["userinfo-mutual_guilds"], value=len(target.mutual_guilds))
            e.add_field(name=d["userinfo-bot"], value=d["true"] if target.bot else d["false"])
            e.add_field(name=d["userinfo-rank"], value=d[f"userinfo-rank-{userdb['rank']}"])
            e.add_field(name=d["userinfo-verified"], value=d["true"] if userdb["verify"] else d["false"])

            roles = target.roles
            roles.reverse()

            e.add_field(name=d["userinfo-roles"], value=", ".join(r.mention for r in roles), inline=False)

            perms = dict(target.guild_permissions)
            val = []
            for k, v in perms.items():
                if v is True:
                    val.append(
                        "`{}`".format(
                            d.get(k, str(k))
                        )
                    )

            e.add_field(
                name=f"{d['userinfo-permissions']} ({target.guild_permissions.value})", 
                value=", ".join(val), 
                inline=False
            )
        else:
            e.add_field(
                name=f"{d['userinfo-public_flags']} ({target.public_flags.value})",
                value=utils.get_public_flags(ctx, target)
            )
            e.add_field(name=d["userinfo-mutual_guilds"], value=len(target.mutual_guilds))
            e.add_field(name=d["userinfo-bot"], value=d["true"] if target.bot else d["false"])
            e.add_field(name=d["userinfo-rank"], value=d[f"userinfo-rank-{userdb['rank']}"])
            e.add_field(name=d["userinfo-verified"], value=d["true"] if userdb["verify"] else d["false"])

        return await m.edit(content=None, embed=e)

def setup(bot):
    bot.add_cog(mido_info(bot))
