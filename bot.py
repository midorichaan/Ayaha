import discord
from discord.ext import commands

import config
from lib import database

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
        
        self.config = config
        self.db = database.Database()
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.resumes = dict()
        self._ext = ["cogs.mido_admins.py", "cogs.mido_bot.py", "cogs.mido_ticket.py", "jishaku"]
        
        for ext in self._ext:
            try:
                self.load_extension(ext)
            except Exception as exc:
                print(f"[Error] Failed to load {ext} → {exc}")
            else:
                print(f"[System] {ext} load")

    #on_command_error
    async def on_command_error(self, ctx, exc):
        pass
    
    #on_command
    async def on_command(self, ctx):
        pass
    
    #on_message
    async def on_message(self, message):
        if message.author.bot:
            return
        
        await self.process_commands(message)
