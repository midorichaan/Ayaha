import discord
from discord.ext import commands

import asyncio

from lib import utils, voiceutils

ffmpeg_options = {
    'before_options': '-loglevel fatal -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

class mido_voice(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        
        if not hasattr(bot, "voice_queue"):
            bot.voice_queue = dict()

    #on_message
    @commands.Cog.listener()
    async def on_message(self, msg):
        if not msg.guild:
            return
        
        if msg.guild.voice_client:
            if self.bot.vars["voice"]["read"]:
                vcqueue = self.bot.voice_queue.get(ctx.guild.id, None)
                ctx = await self.bot.get_context(msg)
                
                if not vcqueue:
                   print(f"[Error] Voice Queue was not found | Guild: {msg.guild}")
                   return 
                
                try:
                    data = await voiceutils.create_source(ctx)
                except Exception as exc:
                    print(f"[Error] {exc}")
                    return
                else:
                    if vcqueue.get("queue", None):
                        vcqueue["queue"].append(data)
                    else:
                        vcqueue["queue"] = [data]
                        self.bot.loop.create_task(
                            self._play(
                                ctx, vcqueue["volume"]
                            )
                        )

    #_play
    async def _play(self, ctx, vol=0.5):
        while self.bot.voice_queue[ctx.guild.id]["queue"]:
            ctx.guild.voice_client.play(
                discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(
                        f"voicereads/{self.bot.queue[ctx.guild.id]['queue'][0]['id']}", 
                        options=ffmpeg_options
                    ), 
                    volume=vol)
            )
            
            try:
                while ctx.guild.voice_client.is_playing() or ctx.guild.voice_client.is_paused():
                    await asyncio.sleep(1)
                    v = ctx.voice_client.source.volume
            except AttributeError:
                pass
            
            self.bot.voice_queue[ctx.guild.id]["queue"].pop(0)

    #voice
    @commands.group(
        name="voice", 
        aliases=["vc"], 
        usage="voice <args>", 
        description="読み上げ関連のコマンドです",
        invoke_without_command=True
    )
    async def voice(self, ctx):
        if not ctx.invoked_subcommand:
            return await utils.reply_or_send(ctx, content="> `/voice help`で使い方を確認してね！")

    #voice help
    @voice.command(
        name="help",
        usage="voice help [command]",
        description="読み上げのヘルプを表示します"
    )
    async def help(self, ctx, command: str=None):
        m = await utils.reply_or_send(ctx, content="> 処理中...")

        if not command:
            e = discord.Embed(
                title="Voice Help",
                color=self.bot.color,
                timestamp=ctx.message.created_at
            )
            
            cmd = self.bot.get_command("voice").commands
            for i in cmd:
                e.add_field(
                    name=i.name, 
                    value=i.description or "説明なし"
                )
                
            return await m.edit(
                content=None,
                embed=e
            )
        else:
            cmd = self.bot.get_command("voice").get_command(command)
            if cmd:
                e = discord.Embed(
                    title=cmd.usage,
                    color=self.bot.color,
                    timestamp=ctx.message.created_at
                )
                e.add_field(name="使用法", value=cmd.usage or "なし")
                e.add_field(name="説明", value=cmd.description or "説明なし")
                e.add_field(name="エイリアス", value=", ".join([f"`{row}`" for row in cmd.aliases]) or "なし")
                return await m.edit(content=None, embed=e)
            
            e = discord.Embed(
                title="Voice Help",
                color=self.bot.color,
                timestamp=ctx.message.created_at
            )
            
            cmd = self.bot.get_command("voice").commands
            for i in cmd:
                e.add_field(
                    name=i.name, 
                    value=i.description or "説明なし"
                )
                
            return await m.edit(
                content=None,
                embed=e
            )

    #voice join
    @voice.command(
        name="join",
        aliases=["start"],
        usage="voice join",
        description="ボイスチャンネルに参加します",
    )
    async def join(self, ctx):
        m = await utils.reply_or_send(ctx, content="> 処理中...")

        if not ctx.author.voice:
            return await m.edit(content=f"> ボイスチャンネルに参加してね！")
        
        if ctx.guild.voice_client:
            return await m.edit(content=f"> {ctx.guild.voice_client.channel.mention}で読み上げ中だよ！")

        try:
            vc = await ctx.author.voice.channel.connect()
        except Exception as exc:
            print(f"[Error] {exc}")
            self.bot.vars["voice"]["read"] = False
            
            if ctx.author.id == self.bot.midorichan.id:
                return await m.edit(content=f"> エラー \n```py\n{exc}\n```")
            else:
                return await m.edit(content="> チャンネル接続中にエラーが発生したよ！")
        else:
            self.bot.vars["voice"]["read"] = True
            self.bot.voice_queue[ctx.guild.id] = {
                "volume": 0.5,
                "queue": []
            }
            return await m.edit(content=f"> {vc.mention}に接続したよ！")

    #voice left
    @voice.command(
        name="left",
        aliases=["stop"],
        usage="voice left",
        description="読み上げを停止し、ボイスチャンネルから退出します"
    )
    async def left(self, ctx):
        m = await utils.reply_or_send(ctx, content="> 処理中...")

        if not ctx.author.voice:
            return await m.edit(content="> ボイスチャンネルに参加してね！")

        if not ctx.guild.voice_client:
            return await m.edit(content="> 読み上げ機能は使われてないよ！")

        vc = ctx.guild.voice_client.channel

        try:
            await ctx.guild.voice_client.disconnect()
        except Exception as exc:
            print(f"[Error] {exc}")
            
            if ctx.author.id == self.bot.midorichan.id:
                return await m.edit(content=f"> エラー \n```py\n{exc}\n```")
            else:
                return await m.edit(content="> チャンネル退出中にエラーが発生したよ！")
        else:
            self.bot.vars["voice"]["read"] = False
            del self.bot.voice_queue[ctx.guild.id]
            return await m.edit(content=f"> {vc.mention}から退出したよ！")

def setup(bot):
    bot.add_cog(mido_voice(bot))
