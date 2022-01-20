import discord
from discord.ext import commands

import json
import urllib.request

from lib import utils

class mido_info(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.jrwlines = {
            "北陸線": "hokuriku",
            "琵琶湖線": "hokurikubiwako",
            "京都線": "kyoto",
            "神戸線": "kobesanyo",
            "赤穂線": "ako",
            "湖西線": "kosei",
            "草津線": "kusatsu",
            "奈良線": "nara",
            "嵯峨野山陰線": "sagano",
            "山陰1線": "sanin1",
            "山陰2線": "sanin2",
            "おおさか東線": "osakahigashi",
            "宝塚線": "takarazuka",
            "福知山線": "fukuchiyama",
            "東西線": "tozai",
            "学研都市線": "gakkentoshi",
            "播但線": "bantan",
            "舞鶴線": "maizuru",
            "大阪環状線": "osakaloop",
            "ゆめ咲線": "yumesaki",
            "大和路線": "yamatoji",
            "阪和線": "hanwahagoromo",
            "関西空港線": "kansaiairport",
            "和歌山2線": "wakayama2",
            "和歌山1線": "wakayama1",
            "万葉まほろば線": "manyomahoroba",
            "関西線": "kansai",
            "きのくに線": "kinokuni",
            "宇野みなと線": "unominato",
            "瀬戸大橋線": "setoohashi",
            "山陽1線": "sanyo1",
            "伯備1線": "hakubi1",
            "可部線": "kabe",
            "山陽2線": "sanyo2",
            "山陽3線": "sanyo3",
            "呉線": "kure",
            "山陰3線": "sanin3",
            "因美線": "imbi1",
            "山陰4線": "sanin4",
            "伯備2線": "hakubi2"
        }

        self.jrwrapids = {
            "大和路快": "大和路快速",
            "丹波路快": "丹波路快速",
            "みやこ快": "みやこ路快速",
            "関空紀州": "関空・紀州路快速",
            "関空快": "関空快速",
            "紀州路快": "紀州路快速",
            "快": "快速",
            "区快": "区間快速",
            "新快": "新快速",
        }

        self.jrwdesti = {
            "関西空港/和歌山方面": "関西空港・和歌山"
        }

    #delay
    @commands.command(name="delay", usage="delay <line>")
    async def delay(self, ctx, line: str=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")

        if not line:
            return await m.edit(content="> {d['args-required']}")

        if not line.endswith("線"):
            line = f"{line}線"

        _ = line
        e = discord.Embed(title=f"{_}の遅延情報", color=self.bot.color, timestamp=ctx.message.created_at)
        line = self.jrwlines.get(line, None)
        if not line:
            return await m.edit(content="> 路線が見つからなかったよ！")

        try:
            ret = urllib.request.urlopen(f"https://www.train-guide.westjr.co.jp/api/v3/{line}.json")
            ret_st = urllib.request.urlopen(f"https://www.train-guide.westjr.co.jp/api/v3/{line}_st.json")
            ret = json.loads(ret.read().decode("utf-8"))
            ret_st = json.loads(ret_st.read().decode("utf-8"))

            p = None
            data = {}

            for s in ret_st["stations"]:
                data[s["info"]["code"]] = s["info"]["name"]
            for i in ret["trains"]:
                if i["delayMinutes"] > 0:
                    st = i["pos"].split("_")

                    try:
                        p = data[st[0]] + "辺り"
                    except KeyError:
                        p = "不明"

                    type = self.jrwrapids.get(i['displayType'], i['displayType'])
                    if "特急" in type:
                        type = type + f" {i['nickname']}"
                    e.add_field(
                        name=f"{type} {self.jrwdesti.get(i['dest']['text'], i['dest']['text'])}行き", 
                        value=f"約{i['delayMinutes']}分遅れ (走行位置: {p})"
                    )

            if not bool(e.fields):
                e.add_field(name="列車遅延", value=d["none"])
            return await m.edit(content=None, embed=e)
        except Exception as exc:
            return await m.edit(conetent=f"> {d['error']} \n```py\n{exc}\n```")

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

                if not profile["exists"]:
                    e.description = f"{predicate(profile['exists'])} Account Exists"
                    return await m.edit(content=None, embed=e)

                banned = data.get("tests", None)
                if not banned:
                    e.description += f"{predicate(profile['exists'])}Account Exists \n{predicate(not profile['protected'])}Account Protected"
                    return await m.edit(content=None, embed=e)

                dates = [
                    f"{predicate(profile['exists'])}Account Exists\n", f"{predicate(profile['protected'])}Account Protected\n",
                    f"{predicate(not banned['ghost']['ban'])}Ghost Ban\n", f"{predicate(banned['search'])}Search Ban\n",
                    f"{predicate(banned['typeahead'])}SearchSuggest Ban\n", f"{predicate(not banned['more_replies'].get('ban', False))}Reply Deboosting\n"
                ]
                for i in dates:
                    e.description += i

                return await m.edit(content=None, embed=e)
        except Exception as exc:
            return await m.edit(content=f"> d['error'] \n```py\n{exc}\n```")

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

    #userinfo
    @commands.command(name="userinfo", aliases=["user", "ui"])
    async def userinfo(self, ctx, target: utils.FetchUserConverter=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")

        if not target:
            target = ctx.author

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
            e.add_field(name=d["userinfo-roles"], value=", ".join(r.mention for r in target.roles.reverse()), inline=False)
            e.add_field(
                name=f"d['userinfo-permissions'] ({target.guild_permissions.value})", 
                value=", ".join(
                    "`{}`".format(
                        d.get(k, str(k)) for k, v in dict(target.guild_permissions).items() if v
                    )
                ), 
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
