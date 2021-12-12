import discord
from discord.ext import commands

import json
import urllib.request

from lib import utils

class mido_info(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.lines = {
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
    
    #delay
    @commands.command(name="delay", usage="delay <line>", description="JR西日本の運行状況を表示します")
    async def delay(self, ctx, line: str=None):
        m = await utils.reply_or_send(ctx, content="> 処理中...")
        
        if not line:
            return await m.edit(content="> 路線を指定してね！")
        
        if not line.endswith("線"):
            line = f"{line}線"
        
        _ = line
        e = discord.Embed(title=f"{_}の遅延情報", color=self.bot.color, timestamp=ctx.message.created_at)
        line = self.lines.get(line, None)
        if not line:
            return await m.edit(content="> 路線が見つからなかったよ！")
        
        try:
            ret = urllib.request.urlopen(f"https://www.train-guide.westjr.co.jp/api/v3/{line}.json")
            ret_st = urllib.request.urlopen(f"https://www.train-guide.westjr.co.jp/api/v3/{line}_st.json")
            ret = json.loads(ret.read().decode("utf-8"))
            ret_st = json.loads(ret_st.read().decode("utf-8"))
            
            p = None
            data = {}
            
            print("a")
            for s in r_st["stations"]:
                data[s["info"]["code"]] = s["info"]["name"]
            print("b")
            for i in r["trains"]:
                if i["delayMinutes"] > 0:
                    st = i["pos"].split("_")
                    
                    try:
                        p = data[st[0]] + "辺り"
                    except KeyError:
                        p = "不明"
                
                    e.add_field(name=f"{i['displayType']} {i['dest']['text']}行き", value=f"約{i['delayMinutes']}分遅れ (現在地: {p})")
            
            print("c")
            if not bool([]):
                e.add_field(name="列車遅延", value="なし")
            return await m.edit(content=None, embed=e)
        except Exception as exc:
            return await m.edit(conetent=f"> エラー \n```py\n{exc}\n```")
    
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
