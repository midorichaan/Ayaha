import discord
from discord.ext import commands
from enum import Enum

import aiohttp
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
            "channel": "test"
        }

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
        webhook_url,
        msg,
        channel,
        username,
        *,
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
        if type == "1":
            try:
                return await self.bot.db.fetchone(query)
            except Exception as exc:
                return exc   
        elif type == "2":
            try:
                return await self.bot.db.fetchall(query)
            except Exception as exc:
                return exc
        elif type == 3:
            try:
                return await self.bot.db.execute(query)
            except Exception as exc:
                return exc

    #send global chat
    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.guild:
            await self.check_db()

            if msg.guild.id == self.sgc["guild_id"]:
                if self.sgc["channel"] == "test":
                    if msg.channel.id == self.sgc["test_channel_id"]:
                        
                elif self.sgc["channel"] == "main":
                    pass
            else:
                try:
                    db = await self.bot.db.fetchone(
                        "SELECT * FROM globalchat WHERE channel_id=%s", 
                        (msg.channel.id,)
                    )
                except Exception as exc:
                    print(f"[Error] {exc}")
                    return
                else:
                    if db:
                        all = await self.bot.db.fetchall(
                            "SELECT * FROM globalchat WHERE channel=%s",
                            (db["channel"],)
                        )

                        

def setup(bot):
    bot.add_cog(mido_global(bot))
