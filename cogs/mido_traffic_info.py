import discord
from discord.ext import commands

from lib import utils, trafficutils

class mido_traffic_info(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.trafficutil = trafficutils.TrafficUtils()

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
