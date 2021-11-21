import discord
from discord.ext import commands, tasks

import aiohttp
import datetime
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
        gs = await bot.db.fetchone("SELECT * FROM guilds WHERE guild_id=%s", (msg.guild.id,))
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
        
        self.owner_id = None
        self.owner_ids = [546682137240403984]
        self.db = database.Database(host=os.environ["DB_ADDRESS"], port=3306, user=os.environ["DB_USERNAME"], password=os.environ["DB_PASSWD"], db=os.environ["DB_NAME"])
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.resumes = dict()
        self.uptime = datetime.datetime.now()
        self.tasks = dict()
        self.langutil = langutil.LangUtil(self)
        self.color = 0xb66767
        self.logger = logging.getLogger("discord")
        self._ext = [
            "cogs.mido_admins", "cogs.mido_help", "cogs.mido_bot", "cogs.mido_user_settings", 
            "cogs.mido_guild_settings", "cogs.mido_ticket", "jishaku"
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
        traceback_exc = ''.join(traceback.TracebackException.from_exception(exc).format())
        print(f"[Error] {ctx.author} → {exc}")
        
        if ctx.guild:
            await self.db.execute("INSERT INTO error_log VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", 
                                  (ctx.message.id, ctx.author.id, ctx.channel.id, ctx.guild.id, 
                                   ctx.message.created_at, ctx.message.content, str(exc), traceback_exc))
        else:
            await self.db.execute("INSERT INTO error_log VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", 
                                  (ctx.message.id, ctx.author.id, ctx.channel.id, None, 
                                   ctx.message.created_at, ctx.message.content, str(exc), traceback_exc))
        
        lang = await self.langutil.get_user_lang(ctx.author.id)
        d = await self.langutil.get_lang(lang)
        
        if isinstance(exc, commands.NotOwner):
            await utils.reply_or_send(ctx, content=f"> {d['notowner']}")
        elif isinstance(exc, commands.CommandNotFound):
            await utils.reply_or_send(ctx, content=f"> {d['cmd-notfound']}")
        elif isinstance(exc, commands.DisabledCommand):
            await utils.reply_or_send(ctx, content=f"> {d['cmd-disabled']}")
        elif isinstance(exc, commands.BadBoolArgument):
            await utils.reply_or_send(ctx, content=f"> {d['exc-badbool']}")
        elif isinstance(exc, commands.NoPrivateMessage):
            await utils.reply_or_send(ctx, content=f"> {d['exc-nodm']}")
        else:
            if ctx.author.id in self.owner_ids:
                await utils.reply_or_send(ctx, content=f"> unknown exception \n```py\n{exc}\n```")
            else:
                await utils.reply_or_send(ctx, content=f"> {d['unknown-exc']}")
                
    #on_command
    async def on_command(self, ctx):
        if ctx.guild:
            print(f"[Log] {ctx.author} → {ctx.message.content} | {ctx.guild} {ctx.channel}")
            await self.db.execute("INSERT INTO command_log VALUES(%s, %s, %s, %s, %s, %s)", 
                                  (ctx.message.id, ctx.author.id, ctx.channel.id, ctx.guild.id, ctx.message.created_at, ctx.message.content))
        else:
            print(f"[Log] {ctx.author} → {ctx.message.content} | @DM")
            await self.db.execute("INSERT INTO command_log VALUES(%s, %s, %s, %s, %s, %s)", 
                                  (ctx.message.id, ctx.author.id, ctx.channel.id, None, ctx.message.created_at, ctx.message.content))
    
    #on_message
    async def on_message(self, message):
        if message.author.bot:
            return
        
        await self.process_commands(message)
    
    #on_ready
    async def on_ready(self):
        print("[System] on_ready!")
        
        await self.change_presence(status=discord.Status.online, 
                                   activity=discord.Game(name=f"-help | Guilds: {len(self.guilds)} | Users: {len(self.users)}")
                                  )
        
        try:
            self.status_update.start()
        except Exception as exc:
            print(f"[Error] {exc}")
        else:
            self.tasks["status_updater"] = self.status_update
            print("[System] Status updater start")
        
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
        self.resumes[shard_id] = datetime.datetime.now()
    
    #on_guild_join
    async def on_guild_join(self, guild):
        db = await self.db.fetchone("SELECT * FROM guilds WHERE guild_id=%s", (guild.id,))
        if not db:
            await self.db.register_guild(guild.id)

    #status update
    @tasks.loop(minutes=10.0)
    async def status_update(self):
        try:
            await self.change_presence(status=discord.Status.online, 
                                       activity=discord.Game(name=f"-help | Guilds: {len(self.guilds)} | Users: {len(self.users)}")
                                      )
        except Exception as exc:
            print(f"[Error] {exc}")
        else:
            print(f"[System] Status updated")
        
    #close
    async def close(self):
        await super().close()
        await self.session.close()
    
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
