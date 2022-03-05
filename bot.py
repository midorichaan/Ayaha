import discord
from discord.ext import commands, tasks

import aiohttp
import datetime
import json
import logging
import os
import traceback

from dotenv import load_dotenv
from lib import database, utils, langutil

#logger
logging.basicConfig(level=logging.WARNING, format="[DebugLog] %(levelname)-8s: %(message)s")

#load .env
load_dotenv()

#_prefix_callable
async def _prefix_callable(bot, msg):
    base = ["-"]

    if msg.guild:
        try:
            gs = await bot.db.fetchone("SELECT * FROM guilds WHERE guild_id=%s", (msg.guild.id,))
        except:
            return base

        if gs["prefix"] != None:
            base.append(gs["prefix"])
        if gs["disable_base_prefix"]:
            base.remove("-")
    return base

class Ayaha(commands.AutoShardedBot):

    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=_prefix_callable,
            intents=intents,
            status=discord.Status.idle,
            shard_count=int(os.environ["SHARD_COUNT"])
        )

        self.banned = []
        self.owner_id = None
        self.owner_ids = [
            449867036558884866, 
            546682137240403984, 
            606693289566928900, 
            635002934907895826
        ]
        self.db = database.Database(
            host=os.environ["DB_ADDRESS"], 
            port=3306, 
            user=os.environ["DB_USERNAME"], 
            password=os.environ["DB_PASSWD"], 
            db=os.environ["DB_NAME"]
        )
        self.session = aiohttp.ClientSession(
            loop=self.loop
        )

        self.langutil = langutil.LangUtil(self)
        self.color = 0xb66767
        self.logger = logging.getLogger("discord")
        self._last_exc = None

        self.vars = {
            "maintenance": False,
            "uptime": datetime.datetime.now(),
            "voice": {
                "read": False,
                "openjtalk": {
                    "path": "",
                    "dictionary": "",
                    "speed": 1.0,
                    "htsvoice": "",
                    "output": "output.txt"
                }
            },
            "pattern": {
                "emoji": r"<:[a-zA-Z0-9_]+:[0-9]+>",
                "discordtoken": r"[a-zA-Z0-9]{24}\.[a-zA-Z0-9]{6}\.[a-zA-Z0-9_\-]{27}|mfa\.[a-zA-Z0-9_\-]{84}"
            },
            "resumes": {
            },
            "tasks": {
            },
            "exc": {
            },
            "fonts": {
                "mushin": "./fonts/mushin.otf"
            },
            "logs": {
                "command": 929845363240747069,
                "error": 929845420425871410,
                "traceback": 929846234599010344,
                "join": 929845441720361011,
                "left": 929845459583905842,
                "request": 929890393573720154
            },
            "support": {
                "id": 929780341382725643,
                "invite": "https://discord.gg/H6u69mt6U9",
                "notice": 929792683180953600
            },
            "globalchat": {
                "noreact": []
            },
            "github_channel_id": 929794199061143552,
            "github_webhook_id": 929799610560573501,
            "time_jst": datetime.timezone(datetime.timedelta(hours=+9), 'JST')
        }

        with open("./lib/publicflags.json", "r") as pf:
            self.vars["publicflags"] = json.load(pf)

        self._ext = [
            "cogs.mido_admins", "cogs.mido_help", "cogs.mido_bot", "cogs.mido_mod", "cogs.mido_user_settings", 
            "cogs.mido_guild_settings", "cogs.mido_ticket", "cogs.mido_info", "cogs.mido_music", "jishaku"
        ]

        for ext in self._ext:
            try:
                self.load_extension(ext)
            except Exception as exc:
                print(f"[Error] failed to load {ext} → {exc}")
            else:
                print(f"[System] {ext} load")

    #on_command_error
    async def on_command_error(self, ctx, exc):
        traceback_exc = ''.join(
            traceback.TracebackException.from_exception(exc).format()
        )
        print(f"[Error] {ctx.author} → {exc}")

        trace = discord.Embed(
            timestamp=ctx.message.created_at,
            color=self.color,
            description=f"```py\n{traceback_exc}\n```"
        )

        guild = self.get_guild(self.vars["support"]["id"])
        tracelog = guild.get_channel(self.vars["logs"]["traceback"])
        await tracelog.send(embed=trace)

        log = discord.Embed(
            timestamp=ctx.message.created_at,
            color=self.color,
            description=f"```py\n{exc}\n```"
        )
        log.add_field(
            name="traceback_id",
            value=f"```\n{tracelog.id}\n```",
            inline=False
        )
        log.set_author(
            name=f"{ctx.author} ({ctx.author.id})", 
            icon_url=ctx.author.avatar_url_as(static_format="png")
        )

        if ctx.guild:
            log.set_footer(
                text=f"{ctx.guild} | {ctx.channel}", 
                icon_url=ctx.guild.icon_url_as(static_format="png")
            )

            try:
                await self.db.execute(
                    "INSERT INTO error_log VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", 
                    (
                        ctx.message.id, ctx.author.id, ctx.channel.id, ctx.guild.id, 
                        ctx.message.created_at, ctx.message.content, str(exc), traceback_exc
                    )
                )
            except Exception as exception:
                print(f"[Error] {exception}")
        else:
            log.set_footer(
                text=f"DM | {ctx.author}", 
            )

            try:
                await self.db.execute(
                    "INSERT INTO error_log VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", 
                    (
                        ctx.message.id, ctx.author.id, ctx.channel.id, None, 
                        ctx.message.created_at, ctx.message.content, str(exc), traceback_exc
                    )
                )
            except Exception as exception:
                print(f"[Error] {exception}")

        exclog = guild.get_channel(self.vars["logs"]["error"])
        await exclog.send(embed=log)

        self.vars["exc"] = {
            "exc": exc,
            "traceback": traceback_exc
        }
        lang = await self.langutil.get_user_lang(ctx.author.id)
        d = await self.langutil.get_lang(lang)

        if isinstance(exc, commands.NotOwner):
            await utils.reply_or_send(ctx, content=f"> {d['exc-notowner']} \n{d['error-id']}: {ctx.message.id}")
        elif isinstance(exc, utils.NotStaff):
            await utils.reply_or_send(ctx, content=f"> {d['exc-notstaff']} \n{d['error-id']}: {ctx.message.id}")
        elif isinstance(exc, commands.CommandNotFound):
            await utils.reply_or_send(ctx, content=f"> {d['exc-cmd-notfound']} \n{d['error-id']}: {ctx.message.id}")
        elif isinstance(exc, commands.DisabledCommand):
            await utils.reply_or_send(ctx, content=f"> {d['exc-cmd-disabled']} \n{d['error-id']}: {ctx.message.id}")
        elif isinstance(exc, commands.BadBoolArgument):
            await utils.reply_or_send(ctx, content=f"> {d['exc-badbool']} \n{d['error-id']}: {ctx.message.id}")
        elif isinstance(exc, commands.NoPrivateMessage):
            await utils.reply_or_send(ctx, content=f"> {d['exc-nodm']} \n{d['error-id']}: {ctx.message.id}")
        elif isinstance(exc, commands.UserNotFound):
            m = d['exc-usernotfound'].replace("{TARGET}", str(exc.argument))
            await utils.reply_or_send(ctx, content=f"> {m} \n{d['error-id']}: {ctx.message.id}")
        elif isinstance(exc, commands.MemberNotFound):
            m = d['exc-membernotfound'].replace("{TARGET}", str(exc.argument))
            await utils.reply_or_send(ctx, content=f"> {m} \n{d['error-id']}: {ctx.message.id}")
        elif isinstance(exc, commands.MissingPermissions):
            perms = ", ".join(exc.missing_perms)
            await utils.reply_or_send(ctx, content=f"> {d['exc-missingperm']} \n{d['require-perms']}: {perms} \n{d['error-id']}: {ctx.message.id}")
        elif isinstance(exc, commands.BotMissingPermissions):
            perms = ", ".join(exc.missing_perms)
            await utils.reply_or_send(ctx, content=f"> {d['exc-botmissingperm']} \n{d['require-perms']}: {perms} \n{d['error-id']}: {ctx.message.id}")
        else:
            if ctx.author.id in self.owner_ids:
                await utils.reply_or_send(ctx, content=f"> {d['exc-unknown']} \n```py\n{exc} \nattrs: {dir(exc)}\n```")
            else:
                await utils.reply_or_send(ctx, content=f"> {d['exc-unknown']} \n{d['error-id']}: {ctx.message.id}")

    #on_command
    async def on_command(self, ctx):
        guild = self.get_guild(self.vars["support"]["id"])
        log = discord.Embed(
            color=self.color,
            timestamp=ctx.message.created_at
        )
        log.set_author(
            name=f"{ctx.author} ({ctx.author.id})",
            icon_url=ctx.author.avatar_url_as(static_format="png")
        )

        if ctx.guild:
            log.set_footer(
                text=f"{ctx.guild} | {ctx.channel}",
                icon_url=ctx.guild.icon_url_as(static_format="png")
            )
            print(f"[Log] {ctx.author} → {ctx.message.content} | {ctx.guild} {ctx.channel}")

            try:
                await self.db.execute(
                    "INSERT INTO command_log VALUES(%s, %s, %s, %s, %s, %s)", 
                    (
                        ctx.message.id, ctx.author.id, ctx.channel.id, ctx.guild.id, ctx.message.created_at, ctx.message.content
                    )
                )
            except Exception as exc:
                print(f"[Error] {exc}")
        else:
            log.set_footer(
                text=f"DM | {ctx.author}",
            )
            print(f"[Log] {ctx.author} → {ctx.message.content} | @DM")

            try:
                await self.db.execute(
                    "INSERT INTO command_log VALUES(%s, %s, %s, %s, %s, %s)", 
                    (
                        ctx.message.id, ctx.author.id, ctx.channel.id, None, ctx.message.created_at, ctx.message.content
                    )
                )
            except Exception as exc:
                print(f"[Error] {exc}")

        log.add_field(
            name="実行時刻",
            value=f"```\n{ctx.message.created_at}\n```"
        )
        log.add_field(
            name="ログID",
            value=f"```\n{ctx.message.id}\n```"
        )
        log.add_field(
            name="実行コマンド",
            value=f"```\n{ctx.message.content}\n```",
            inline=False
        )
        await guild.get_channel(self.vars["logs"]["command"]).send(embed=log)

    #on_message
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.author.id in self.banned:
            return

        if not self.vars["maintenance"]:
            await self.process_commands(message)
        else:
            if message.author.id in self.owner_ids:
                await self.process_commands(message)

    #on_ready
    async def on_ready(self):
        print("[System] on_ready!")

        for i in self.guilds:
            try:
                await utils.check_guild_profile(self, i.id)
            except:
                pass

        try:
            db = await self.db.fetchall("SELECT * FROM users WHERE rank=3")
        except Exception as exc:
            print(f"[Error] {exc}")
            self.owner_ids = [546682137240403984, 635002934907895826, 449867036558884866]
        else:
            self.owner_ids = [i["user_id"] for i in db]

        await self.change_presence(
            status=discord.Status.online, 
            activity=discord.Game(
                name=f"-help | Guilds: {len(self.guilds)} | Users: {len(self.users)}"
            )
        )

        try:
            self.status_update.start()
        except Exception as exc:
            print(f"[Error] {exc}")
        else:
            self.vars["tasks"]["status_updater"] = self.status_update
            print("[System] Status updater start")

        try:
            db = await self.db.fetchall("SELECT * FROM banned")
        except Exception as exc:
            print(f"[Error] {exc}")
            self.banned = []
        else:
            self.banned = [i["user_id"] for i in db]
            print("[System] set prohibit users")
        
        print("[System] enabled midori-dbot!")

    #on_connect
    async def on_connect(self):
        print("[System] on_connect!")

    #on_shard_ready
    async def on_shard_ready(self, shard_id):
        print(f"[System] shard {shard_id} ready")

    #on_shard_resumed
    async def on_shard_resumed(self, shard_id):
        print(f"[System] shard {shard_id} has resumed")
        self.vars["resumes"][shard_id] = datetime.datetime.now()

    #on_guild_join
    async def on_guild_join(self, guild):
        try:
            await self.db.register_guild(guild.id)
        except Exception as exc:
            print(f"[Error] {exc}")

        log = discord.Embed(
            title="Guild Join Log",
            color=self.color,
            timestamp=datetime.datetime.now()
        )
        log.add_field(
            name="サーバー名",
            value=f"```\n{guild.name}\n```"
        )
        log.add_field(
            name="サーバーオーナー",
            value=f"```\n{guild.owner} ({guild.owner.id})\n```"
        )
        log.add_field(
            name="サーバー作成日時",
            value=f"```\n{guild.created_at}\n```"
        )
        members = len(guild.members)
        channels = len(guild.channels)
        text = len([i for i in guild.channels if isinstance(i, discord.TextChannel)])
        voice = len([i for i in guild.channels if isinstance(i, discord.VoiceChannel)])
        log.add_field(
            name="その他",
            value=f"```\nメンバー数: {members}\nチャンネル数: {channels}\nテキストチャンネル: {text}\nボイスチャンネル: {voice}\n```"
        )

        guild = self.get_guild(self.vars["support"]["id"])
        channel = guild.get_channel(self.vars["logs"]["join"])
        await channel.send(embed=log)

    #on_guild_remove
    async def on_guild_remove(self, guild):
        try:
            await self.db.unregister_guild(guild.id)
        except Exception as exc:
            print(f"[Error] {exc}")

        log = discord.Embed(
            title="Guild Left Log",
            color=self.color,
            timestamp=datetime.datetime.now()
        )
        log.add_field(
            name="サーバー名",
            value=f"```\n{guild.name}\n```"
        )
        log.add_field(
            name="サーバーオーナー",
            value=f"```\n{guild.owner} ({guild.owner.id})\n```"
        )
        log.add_field(
            name="サーバー作成日時",
            value=f"```\n{guild.created_at}\n```"
        )
        members = len(guild.members)
        channels = len(guild.channels)
        text = len([i for i in guild.channels if isinstance(i, discord.TextChannel)])
        voice = len([i for i in guild.channels if isinstance(i, discord.VoiceChannel)])
        log.add_field(
            name="その他",
            value=f"```\nメンバー数: {members}\nチャンネル数: {channels}\nテキストチャンネル: {text}\nボイスチャンネル: {voice}\n```"
        )

        guild = self.get_guild(self.vars["support"]["id"])
        channel = guild.get_channel(self.vars["logs"]["left"])
        await channel.send(embed=log)

    #status update
    @tasks.loop(minutes=10.0)
    async def status_update(self):
        if not self.vars["maintenance"]:
            try:
                await self.change_presence(
                    status=discord.Status.online, 
                    activity=discord.Game(
                        name=f"-help | Guilds: {len(self.guilds)} | Users: {len(self.users)}"
                    )
                )
            except Exception as exc:
                print(f"[Error] {exc}")
            else:
                print(f"[System] Status updated")

    #close
    async def close(self):
        await self.session.close()
        await super().close()

    #run
    def run(self):
        try:
            super().run(os.environ["BOT_TOKEN"])
        except Exception as exc:
            print(f"[Error] {exc}")
        else:
            print("[System] enabling....")

bot = Ayaha()
bot.run()
