import discord
from discord.ext import commands
from enum import Enum

import aiohttp
import asyncio
import re

class DBType(Enum):
    FETCHONE = 1
    FETCHALL = 2
    EXECUTE = 3

class mido_global(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, "session"):
            bot.session = aiohttp.ClientSession()
        self.session = bot.session

        self.badges = {
            "staff": "🔒",
            "verify": "💠",
            "member": "👤",
            "bot": "🛠️",
            "partner": "🤝",
            "vip": "💎",
            "sgc_mods": "🔨"
        }

        self.react = {
            "exc": "❌",
            "success": "✅"
        }

        self.sgc = {
            "guild_id": 706905953320304772,
            "channel_id": 707158257818664991,
            "test_channel_id": 707158343952629780,
            "channel": "test",
            "mod_ids": []
        }

        guild = self.bot.get_guild(self.sgc["guild_id"])
        if guild:
            role = guild.get_role(795213916204564492)
            self.sgc["mod_ids"] = [i.id for i in role.members]

        self.enabled = True

    ####events
    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        db = await self.get_db(
            DBType.FETCHONE, 
            query=f"SELECT * FROM guilds WHERE channel_id={channel.id}"
        )

        if db and not isinstance(db, Exception):
            me = channel.guild.get_member(self.bot.user.id)
            cp = channel.permissions_for(me)
            if cp.manage_webhooks:
                hook = discord.utils.get(
                    await channel.webhooks(),
                    name="ayaha-global"
                )
                if not hook:
                    await self.get_db(
                        DBType.EXECUTE, 
                        query=f"DELETE FROM globalchat WHERE channel_id={channel.id}"
                    )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        db = await self.get_db(
            DBType.FETCHALL,
            query=f"SELECT * FROM globalchat WHERE guild_id={guild.id}"
        )

        if db and not isinstance(db, Exception):
            await self.get_db(
                DBType.EXECUTE,
                query=f"DELETE FROM globalchat WHERE guild_id={guild.id}"
            )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        db = await self.get_db(
            DBType.FETCHONE,
            query=f"SELECT * FROM globalchat WHERE channel_id={channel.id}"
        )

        if db and not isintance(db, Exception):
            await self.get_db(
                DBType.EXECUTE,
                query=f"DELETE FROM globalchat WHERE channel_id={channel.id}"
            )

    ####globalchat utils
    def check_content(self, msg):
        invite_regex = re.compile(r'(?:https?\:\/\/)?discord(?:\.gg|(?:app)?\.com\/invite)\/([a-zA-Z0-9]+)')
        mention_regex = re.compile(r'<@!*&*[0-9]+>')

        if isinstance(msg, discord.Message):
            if msg.mention_everyone:
                return False
            if len(msg.mentions) >= 5:
                return False
            if invite_regex.findall(msg.content):
                return False
            if "@here" in msg.content:
                return False
            if "@everyone" in msg.content:
                return False
        else:
            if "@here" in msg:
                return False
            if "@everyone" in msg:
                return False
            if invite.regex.findall(msg):
                return False
            if len(mention_regex.findall(msg)) >= 5:
                return False
        return True

    def check_reaction(self, channel_id):
        if channel_id in self.bot.vars["globalchat"]["noreact"]:
            return True
        return False

    async def global_send(
        self, 
        *,
        webhook_url,
        msg,
        channel,
        username,
        embeds=None
    ):
        hook = discord.Webhook.from_url(
            webhook_url,
            adapter=discord.AsyncWebhookAdapter(self.session)
        )

        embed = None
        attachment = None

        if msg.embeds:
            embed = msg.embeds
        if msg.attachments:
            attachments = [await i.to_file() for i in msg.attachments]

        if embed:
            message = await hook.send(
                msg.clean_content,
                username=username,
                avatar_url=msg.author.avatar_url_as(static_format="png"),
                embeds=embed,
                file=attachments,
                wait=True
            )
        else:
            message = await hook.send(
                msg.clean_content,
                username=username,
                avatar_url=msg.author.avatar_url_as(static_format="png"),
                files=attachments,
                wait=True
            )
        return (message.id, msg.id, msg.guild.id, msg.channel.id, msg.author.id, str(msg.content), channel)

    async def check_db(self):
        try:
            await self.bot.db.execute("SELECT 1")
        except:
            self.enabled = False
        else:
            self.enabled = True

    async def get_db(self, type, *, query):
        if type == DBType.FETCHONE:
            try:
                return await self.bot.db.fetchone(query)
            except Exception as exc:
                return exc   
        elif type == DBType.FETCHALL:
            try:
                return await self.bot.db.fetchall(query)
            except Exception as exc:
                return exc
        elif type == DBType.EXECUTE:
            try:
                return await self.bot.db.execute(query)
            except Exception as exc:
                return exc

    #get_rank
    def get_rank(self, user, db):
        ret = ""
        if db["rank"] == 2:
            ret += self.badges["staff"]
        if db["rank"] <= 1:
            ret += self.badges["vip"]
        if db["verify"] == 1:
            ret += self.badges["verify"]
        if db["partner"] == 1:
            ret += self.badges["partner"]
        if user.id in self.sgc["mod_ids"]:
            ret += self.badges["sgc_mods"]
        if user.bot:
            ret += self.badges["bot"]
        else:
            ret += self.badges["member"]

        return f"{ret}{user}"

    #get_tasks
    async def get_tasks(self, msg, *, userdb, channel: str):
        db = await self.get_db(
            DBType.FETCHALL,
            query=f"SELECT * FROM globalchat WHERE channel={channel}"
        )
        if not db:
            return []

        task = []
        username = self.get_rank(msg.author, userdb)
        for i in db:
            task.append(
                self.global_send(
                    webhook_url=i["webhook_url"],
                    msg=msg,
                    channel=channel,
                    username=username,
                    embeds=msg.embeds
                )
            )
        return task

    #handle_global
    async def handle_global(self, *, task):
        try:
            await asyncio.gather(*task)
        except Exception as exc:
            print(f"[Error] {exc}")

    #send global chat
    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.guild:
            await self.check_db()
            if not self.enabled:
                return

            userdb = await self.get_db(
                DBType.FETCHONE,
                query=f"SELECT * FROM users WHERE user_id={msg.author.id}"
            )

            if msg.channel.id if [self.sgc["test_channel_id"], self.sgc["channel_id"]]:
                check = self.check_content(msg)
                

                tasks = await self.get_tasks(msg, userdb=userdb, channel="sgc")
                try:
                    return await self.handle_global(task=tasks)
                except Exception as exc:
                    print(f"[Error] {exc}")
                    return
                 
def setup(bot):
    bot.add_cog(mido_global(bot))
