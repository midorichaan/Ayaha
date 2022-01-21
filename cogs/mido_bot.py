import discord
from discord.ext import commands

import datetime
import time

from lib import utils

class mido_bot(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, "wait_for_reply"):
            bot.wait_for_reply = {}

        self.github_cache = {}

    #github_cache
    @commands.Cog.listener("on_message")
    async def github_cache_creator(self, msg):
        if msg.channel.id == self.bot.vars["github_channel_id"]:
            if msg.author.id != self.bot.vars["github_webhook_id"]:
                pass

            try:
                logs = await logch.history(limit=25).flatten()                 
                logs.reverse()
            except Exception as exc:
                print(f"[Error] failed to create github cache → {exc}")
            else:
                e = discord.Embed(
                    title="Github Commits",
                    color=self.bot.color,
                    timestamp=ctx.message.created_at
                )

                for i in logs:
                    if i.author.id == self.bot.vars["github_webhook_id"]:
                        e.add_field(
                            name="**{}**".format(i.embeds[0].title),
                            value="{} \n{}".format(
                                i.embeds[0].description, 
                                datetime.datetime.fromtimestamp(
                                    i.created_at.timestamp(), 
                                    self.bot.vars["time_jst"]
                                ).strftime("%Y/%m/%d %H:%M:%S")
                            )
                        )
                logs.reverse()
                e.set_footer(text="Last Commit")
                e.timestamp = logs[0].created_at

                self.github_cache["embed"] = e
                self.github_cache["message_data"] = logs

    #on_msg
    @commands.Cog.listener()
    async def on_message(self, msg):
        if not msg.guild:
            return

        if msg.guild.id == self.bot.vars["support"]["id"]:
            if msg.channel.id == self.bot.vars["logs"]["request"]:
                admin_ids = [i.id for i in msg.guild.get_role(929780897052516392).members]
                if msg.author.id in admin_ids:
                    if msg.reference:
                        m = self.bot.wait_for_reply.get(msg.reference.resolved.id, None)
                        if not m:
                            return
                        if m["resolved"]:
                            return

                        lang = await self.bot.langutil.get_lang(m["userlang"])
                        m["resolved"] = True
                        try:
                            await m["message"].reply(content=f"> {lang['admin-reply']} \n```\n{msg.content}\n``` \n{msg.author}")
                        except:
                            await m["message"].send(content=f"> {lang['admin-reply']} \n```\n{msg.content}\n``` \n{msg.author} \n→ <{msg.jump_url}>")

    #github
    @commands.command(name="github", usage="github [commit hash]")
    async def github(self, ctx, commit: str=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")

        logch = self.bot.get_channel(self.bot.vars["github_channel_id"])
        if not logch:
            return await m.edit(content=f"> {d['exc-cant_fetch-data']}")

        if commit:
            return await m.edit(content=None, embed=self.github_cache["embed"])
        else:
            return await m.edit(content=None, embed=self.github_cache["embed"])

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
            name=d["library"],
            value=f"discord.py v{discord.__version__}"
        )
        e.add_field(
            name=d["name"],
            value="桜井 彩葉 / Ayaha Sakurai"
        )
        e.add_field(
            name=d["supportsrv"],
            value=self.bot.vars["support"]["invite"],
            inline=False
        )
        e.add_field(
            name=d["invites"], 
            value="https://discord.com/oauth2/authorize?client_id=911139204531122257&scope=bot+applications.commands", 
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

        guild = self.bot.get_guild(self.bot.vars["support"]["id"])
        dm = await guild.get_channel(self.bot.vars["logs"]["request"]).send(embed=e)

        self.bot.wait_for_reply[dm.id] = {
            "message": m,
            "userlang": lang,
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

        guild = self.bot.get_guild(self.bot.vars["support"]["id"])
        dm = await guild.get_channel(self.bot.vars["logs"]["request"]).send(embed=e)

        self.bot.wait_for_reply[dm.id] = {
            "message": m,
            "userlang": lang,
            "resolved": False
        }
        return await m.edit(content="> {}".format(d["request-submited"]))

    #invite
    @commands.command(usage="invite")
    async def invite(self, ctx):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")

        return await m.edit(content=f"> {d['invites']} \n<https://discord.com/oauth2/authorize?client_id=911139204531122257&scope=bot+applications.commands>")

def setup(bot):
    bot.add_cog(mido_bot(bot))
