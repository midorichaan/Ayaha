import discord
from discord.ext import commands

import urllib, json

from lib import utils, trafficutils

class mido_traffic_info(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.trafficutil = trafficutils.TrafficUtils()
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

        self.jrwlinelists = {
            "wakayama1": "和歌山線 (五条 〜 和歌山)",
            "wakayama2": "和歌山線 (王寺 〜 五条)",
            "sanin1": "山陰線 (園部 〜 福知山)",
            "sanin2": "山陰線 (福知山 〜 居組)",
            "sanin3": "山陰線 (諸寄 〜 米子)",
            "sanin4": "山陰線 (米子 〜 益田)",
            "sanyo1": "山陽線 (上郡 〜 三原)",
            "sanyo2": "山陽線 (糸崎 〜 南岩国)",
            "sanyo3": "山陽線 (岩国 〜 下関)",
            "hakubi1": "伯備線 (倉敷 〜 新郷)",
            "hakubi2": "伯備線 (新郷 〜 伯耆大山)"
        }

        self.jrwrapids = {
            "大和路快": "大和路快速",
            "丹波路快": "丹波路快速",
            "みやこ快": "みやこ路快速",
            "関空紀州": "関空・紀州路快速",
            "関空快": "関空快速",
            "紀州路快": "紀州路快速",
            "快": "快速",
            "直快": "直通快速",
            "区快": "区間快速",
            "新快": "新快速",
            "特": "特急",
            "普通2": "普通 (JRゆめ咲線直通)"
        }

        self.jrwdesti = {
            "関西空港/和歌山方面": "関西空港・和歌山"
        }

    #generate_help
    def generate_help(self, ctx, data, *, command=None):
        if command:
            e = discord.Embed(title=f"Help - {command}", color=self.bot.color, timestamp=ctx.message.created_at)
            e.add_field(name=data["usage"], value=command.usage or data["none"])
            e.add_field(name=data["description"], value=data.get(f"help-{command.name}", data["none"]))
            e.add_field(name=data["aliases"], value=", ".join([f"`{row}`" for row in command.aliases]) or data["no-aliases"])
            return e
        else:
            e = discord.Embed(title=f"Help - Commands", color=self.bot.color, timestamp=ctx.message.created_at)

            for i in self.bot.get_command("trafficinfo").commands:
                e.add_field(name=i.name, value=data.get(f"help-{i.name}", data["none"]))
            return e

    #trafficinfo
    @commands.group(name="trafficinfo", aliases=["ti", "traffic"], usage="trafficinfo <args>")
    async def trafficinfo(self, ctx):
        if ctx.invoked_subcommand is None:
            lang = await self.bot.langutil.get_user_lang(ctx.author.id)
            d = await self.bot.langutil.get_lang(lang)
            m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")
            await m.edit(content=f"> {d['trafficinfo-view-help']}")

    #trafficinfo help
    @trafficinfo.command(name="help", usage="help [command]")
    async def help(self, ctx, *, command: str=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")

        if command:
            cmd = self.bot.get_command(command)
            if not cmd:
                e = self.generate_help(ctx, d)
                return await m.edit(content=None, embed=e)
            else:
                e = self.generate_help(ctx, d, command=cmd)
                return await m.edit(content=None, embed=e)
        else:
            e = self.generate_help(ctx, d)
            return await m.edit(content=None, embed=e)

    #trafficinfo delay
    @trafficinfo.command(name="delay", usage="delay <line>")
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


def setup(bot):
    bot.add_cog(mido_traffic_info(bot))
