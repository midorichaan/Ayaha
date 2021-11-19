import discord
from discord.ext import commands

import aiohttp
import datetime
import traceback

import config
from lib import database, utils, langutil

#_prefix_callable
def _prefix_callable(bot, msg):
    return ["-"]
        
class TicketBot(commands.AutoShardedBot):
    
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=_prefix_callable,
            intents=intents,
            status=discord.Status.idle,
            shard_count=config.SHARD_COUNT
        )
        
        self.owner_id = None
        self.owner_ids = config.OWNER_IDS
        self.config = config
        self.db = database.Database()
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.resumes = dict()
        self._ext = ["cogs.mido_admins", "cogs.mido_bot", "cogs.mido_ticket", "jishaku"]
        self.uptime = datetime.datetime.now()
        self.tasks = dict()
        self.langutil = langutil.LangUtil(self)
        
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
        
        if ctx.guild:
            await self.db.execute("INSERT INTO error_log VALUES(%s, %s, %s, %s, %s, %s)", 
                                  (ctx.message.id, ctx.author.id, ctx.channel.id, ctx.guild.id, 
                                   ctx.message.created_at, ctx.message.content, exc, traceback_exc))
        else:
            await self.db.execute("INSERT INTO error_log VALUES(%s, %s, %s, %s, %s, %s)", 
                                  (ctx.message.id, ctx.author.id, ctx.channel.id, None, 
                                   ctx.message.created_at, ctx.message.content, exc, traceback_exc))
        
        if isinstance(exc, commands.NotOwner):
            await utils.reply_or_send(ctx, content=f"> {await self.langutil.get_lang(ctx.author, key='notowner')}")
        elif isinstance(exc, commands.CommandNotFound):
            await utils.reply_or_send(ctx, content=f"> {await self.langutil.get_lang(ctx.author.id, key='cmd-notfound')}")
        elif isinstance(exc, commands.DisabledCommand):
            await utils.reply_or_send(ctx, content=f"> {await self.langutil.get_lang(ctx.author.id, key='cmd-disabled')}")
        elif isinstance(exc, commands.BadBoolArgument):
            await utils.reply_or_send(ctx, content=f"> {await self.langutil.get_lang(ctx.author.id, key='exc-badbool')}")
        else:
            if ctx.author.id in self.owner_ids:
                await utils.reply_or_send(ctx, content=f"> unknown exception \n```py\n{exc}\n```")
            else:
                await utils.reply_or_send(ctx, content=f"> {await self.langutil.get_lang(ctx.author.id, key='unknown-exc')}")
                
    #on_command
    async def on_command(self, ctx):
        if ctx.guild:
            await self.db.execute("INSERT INTO command_log VALUES(%s, %s, %s, %s, %s, %s)", 
                                  (ctx.message.id, ctx.author.id, ctx.channel.id, ctx.guild.id, ctx.message.created_at, ctx.message.content))
        else:
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
            super().run(config.BOT_TOKEN)
        except Exception as exc:
            print(f"[Error] {exc}")
        else:
            print("[System] enabling....")

bot = TicketBot()
bot.run()
