import discord
from discord.ext import commands

import pyqrcode
import re
from lib import utils

class mido_funny(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.__url_regex_str = "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        self.__url_regex = re.compile(self.__url_regex_str)

    #qrcode
    @commands.command(name="qrcode", aliases=["qr"])
    async def _qrcode(self, ctx, *, url: str=None):
        m = await utils.reply_or_send(ctx, content="> 処理中...")

        if not url.startswith("http"):
            url = "https://" + url

        if not self.__url_regex.match(url):
            return await m.edit(content=f"> URLを指定してね！")

        try:
            ret = pyqrcode.QRCode(url, error="M")
            ret.png(f"/qrcode/{ctx.author.id}.png", scale=6)
        except Exception as exc:
            return await m.edit(content=f"> エラー \n```py\n{exc}\n```")
        else:
            img = discord.File(f"/qrcode/{ctx.author.id}.png")
            return await m.edit(content="> 作成しました！", file=img)

def setup(bot):
    bot.add_cog(mido_funny(bot))
