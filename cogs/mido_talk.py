import discord
from discord.ext import commands

import random
from lib import utils

class mido_talk(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._cache = []

        self.cache_updater.start()

    def cog_unload(self):
        self.cache_updater.cancel()

    @tasks.loop(minutes=10.0)
    async def cache_updater(self):
        try:
            db = await self.bot.db.fetchall(
                "SELECT * FROM talk"
            )
        except Exception as exc:
            self.bot.logger.warning(f"TASK: {exc}")
        else:
            self.bot.logger.info("TASK: Talk cache updated")
            self._cache = [i["word"] for i in db]

    #check_talk
    async def check_talk(self, msg) -> bool:
        if not msg.guild:
            return False

        gs = await self.bot.db.fetchone(
            "SELECT * FROM guilds WHERE guild_id=%s",
            (msg.guild.id,)
        )
        if not gs:
            return False
        if gs["talk"] == 0:
            return False
        return True

    #listener
    @commands.Cog.listener()
    async def on_message(self, msg):
        check = await self.check_talk(msg)
        if not check:
            return

        i = random.choice(self._cache)
        if i:
            await utils.reply_or_send(i)

def setup(bot):
    bot.add_cog(mido_talk(bot))
