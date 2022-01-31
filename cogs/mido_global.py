import discord
from discord.ext import commands

import aiohttp
import re

class mido_global(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session or aiohttp.ClientSession()

        self.badges = {
            "staff": "🔒",
            "verify": "💠",
            "member": "👤",
            "bot": "🛠️",
            "partner": "🤝",
            "sgc_mods": "🔨"
        }

        self.sgc = {
            "guild_id": 706905953320304772,
            "channel_id": 707158257818664991,
            "test_channel_id": 707158343952629780,
            "channel": "test"
        }

    ####events
    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        try:
            db = await self.bot.db.fetchone(
                "SELECT * FROM globalchat WHERE channel_id=%s",
                (channel.id,)
            )
        except Exception as exc:
            print(f"[Error] {exc}")
            return
        else:
            if db:
                me = channel.guild.get_member(self.bot.user.id)
                cp = channel.permissions_for(me)
                if cp.manage_webhooks:
                    hook = discord.utils.get(
                        await channel.webhooks(),
                        name="ayaha-global"
                    )
                    if not hook:
                        try:
                            await self.bot.db.execute(
                                "DELETE FROM globalchat WHERE channel_id=%s",
                                (channel.id,)
                            )
                        except Exception as exc:
                            print(f"[Error] {exc}")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        try:
            db = await self.bot.db.fetchall(
                "SELECT * FROM globalchat WHERE guild_id=%s",
                (guild.id,)
            )
        except Exception as exc:
            print(f"[Error] {exc}")
            return
        else:
            if db:
                try:
                    await self.bot.db.execute(
                        "DELETE FROM globalchat WHERE guild_id=%s",
                        (guild.id,)
                    )
                except Exception as exc:
                    print(f"[Error] {exc}")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        try:
            db = await self.bot.db.fetchone(
                "SELECT * FROM globalchat WHERE channel_id=%s",
                (channel.id,)
            )
        except Exception as exc:
            print(f"[Error] {exc}")
            return
        else:
            if db:
                try:
                    await self.bot.db.execute(
                        "DELETE FROM globalchat WHERE channel_id=%s",
                        (channel.id,)
                    )
                except Exception as exc:
                    print(f"[Error] {exc}")
                    return

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

    

def setup(bot):
    bot.add_cog(mido_global(bot))
