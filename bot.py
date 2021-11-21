import discord
from discord.ext import commands

import aiohttp
import datetime
import os
import traceback

from dotenv import load_dotenv
from lib import database, utils, langutil

#load .env
load_dotenv()

#_prefix_callable
def _prefix_callable(bot, msg):
    return ["-"]
        
class Ayaha(commands.AutoShardedBot):
    
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=_prefix_callable,
            intents=intents,
            status=discord.Status.idle,
            shard_count=os.environ["SHARD_COUNT"]
        )
        
        self.owner_id = None
        self.owner_ids = os.environ["OWNER_IDS"]
        self.db = database.Database()
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.resumes = dict()
        self._ext = ["cogs.mido_admins", "cogs.mido_bot", "cogs.mido_ticket", "jishaku"]
        self.uptime = datetime.datetime.now()
        self.tasks = dict()
        self.langutil = langutil.LangUtil(self)
        self.color = 0xb66767
        
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
        
        if isinstance(exc, commands.NotOwner):
            lang = await self.langutil.get_lang(ctx.author, key='notowner')
            await utils.reply_or_send(ctx, content=f"> {lang}")
        elif isinstance(exc, commands.CommandNotFound):
            lang = await self.langutil.get_lang(ctx.author, key='cmd-notfound')
            await utils.reply_or_send(ctx, content=f"> {lang}")
        elif isinstance(exc, commands.DisabledCommand):
            lang = await self.langutil.get_lang(ctx.author, key='cmd-disabled')
            await utils.reply_or_send(ctx, content=f"> {lang}")
        elif isinstance(exc, commands.BadBoolArgument):
            lang = await self.langutil.get_lang(ctx.author, key='exc-badbool')
            await utils.reply_or_send(ctx, content=f"> {lang.replace('{REPLACE}', exc.argument)}")
        else:
            if ctx.author.id in self.owner_ids:
                await utils.reply_or_send(ctx, content=f"> unknown exception \n```py\n{exc}\n```")
            else:
                lang = await self.langutil.get_lang(ctx.author.id, key='unknown-exc')
                await utils.reply_or_send(ctx, content=f"> {lang}")
                
    #on_command
    async def on_command(self, ctx):
        if ctx.guild:
            print(f"[System] {ctx.author} → {ctx.message.content} | {ctx.guild} {ctx.channel}")
            await self.db.execute("INSERT INTO command_log VALUES(%s, %s, %s, %s, %s, %s)", 
                                  (ctx.message.id, ctx.author.id, ctx.channel.id, ctx.guild.id, ctx.message.created_at, ctx.message.content))
        else:
            print(f"[System] {ctx.author} → {ctx.message.content} | @DM")
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
