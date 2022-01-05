import discord
from discord.ext import commands

import time

from lib import utils

class mido_bot(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, "wait_for_reply"):
            bot.wait_for_reply = {}

    #on_msg
    @commands.Cog.listener()
    async def on_message(self, msg):
        if isinstance(msg.channel, discord.DMChannel):
            if msg.author.id == 546682137240403984:
                if msg.reference:
                    m = self.bot.wait_for_reply.get(msg.reference.resolved.id, None)
                    if not m:
                        return
                    if m["resolved"]:
                        return

                    m["resolved"] = True
                    try:
                        await m["message"].reply(content=f"> 運営からの回答 \n```\n{msg.content}\n```")
                    except:
                        await m["message"].send(content=f"> 運営からの回答 \n```\n{msg.content}\n``` \n→ <{msg.jump_url}>")

    #ping
    @commands.command(usage="ping")
    async def ping(self, ctx):
        msg_time = time.perf_counter()

        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['ping-pinging']}")

        ws = round(self.bot.latency * 1000, 2)
        ping = round(time.perf_counter() - msg_time, 3) * 1000
        await m.edit(content=f"> {d['ping-pong']} \nPing: {ping}ms \nWebSocket: {ws}ms")

    #about
    @commands.command(aliases=["info", "bot", "ayaha"], usage="about")
    async def about(self, ctx):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)

        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")

        e = discord.Embed(
            title=d["about-ayaha"], 
            description=d["about-ayaha-description"], 
            color=self.bot.color, 
            timestamp=ctx.message.created_at
        )
        e.add_field(
            name=d["guilds"], 
            value=str(len(self.bot.guilds))
        )
        e.add_field(
            name=d["users"], 
            value=str(len(self.bot.users))
        )
        e.add_field(
            name=d["name"],
            value="-- 彩葉 / Ayaha --"
        )
        e.add_field(
            name=d["invites"], 
            value="https://discord.com/oauth2/authorize?client_id=911139204531122257&scope=bot", 
            inline=False
        )
        await m.edit(content=None, embed=e)

    #report
    @commands.command(usage="report <content>")
    async def report(self, ctx, *, content: str=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)

        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")

        if not content:
            return await m.edit(content=f"> {d['args-required']}")

        e = discord.Embed(
            description=f"__**Report**__ \n```\n{content}\n```", 
            color=self.bot.color, 
            timestamp=ctx.message.created_at
        )
        e.set_author(
            name=f"{ctx.author} ({ctx.author.id})", 
            icon_url=ctx.author.avatar_url_as(static_format="png")
        )
        dm = await self.bot.get_user(546682137240403984).send(embed=e)

        self.bot.wait_for_reply[dm.id] = {
            "message": m,
            "resolved": False
        }

        return await m.edit(content="> {}".format(d["report-submited"]))

    #request
    @commands.command(name="request", aliases=["feature"], usage="request <content>")
    async def request(self, ctx, *, content: str=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)

        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")

        if not content:
            return await m.edit(content=f"> {d['args-required']}")

        e = discord.Embed(
            description=f"__**Request**__ \n```\n{content}\n```", 
            color=self.bot.color, 
            timestamp=ctx.message.created_at
        )
        e.set_author(
            name=f"{ctx.author} ({ctx.author.id})", 
            icon_url=ctx.author.avatar_url_as(static_format="png")
        )
        dm = await self.bot.get_user(546682137240403984).send(embed=e)

        self.bot.wait_for_reply[dm.id] = {
            "message": m,
            "reply": False
        }

        return await m.edit(content="> {}".format(d["request-submited"]))

    #invite
    @commands.command(usage="invite")
    async def invite(self, ctx):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)

        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")
        return await m.edit(content=f"> {d['invites']} \n<https://discord.com/oauth2/authorize?client_id=911139204531122257&scope=bot>")

def setup(bot):
    bot.add_cog(mido_bot(bot))
