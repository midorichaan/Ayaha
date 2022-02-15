import discord
from discord.ext import commands

import datetime
import io

class mido_logs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.colors = {
            "info": 0x3498db,
            "warn": 0xf1c40f,
            "error": 0xff0000
        }

    #send_log
    async def send_log(self, channel, *args, **kwargs):
        try:
            msg = await channel.send(embed=embed)
        except Exception as exc:
            print(f"[Error] {exc}")
            return None
        else:
            return msg

    #on_message_delete
    @commands.Cog.listener()
    async def on_message_delete(self, msg):
        embed = discord.Embed(
            title="Log - MessageDelete",
            color=self.colors["error"],
            timestamp=datetime.datetime.now()
        )

        attachments = None
        if msg.attachments:
            attachments = "".join(f"{i.url}\n" for i in msg.attachments)
            attachments = discord.File(
                fp=io.StringIO(attachments),
                filename="attachments.txt"
            )
            

        embed.add_field(name="メッセージ送信者", value=f"{msg.author} (ID: {msg.author.id})")
        embed.add_field(name="チャンネル", value=f"{msg.channel if msg.channel else 'unknown'}")

        if msg.content:
            if len(msg.content) >= 1010:
                embed.add_field(name="メッセージ内容", value=f"```\n{msg.content}\n...\n```", inline=False)
            else:
                embed.add_field(name="メッセージ内容", value=f"```\n{msg.content}\n```", inline=False)[]

def setup(bot):
    bot.add_cog(mido_logs(bot))
