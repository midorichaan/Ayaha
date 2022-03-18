import discord
import functools
from discord.ext import commands

import asyncio
import os
import youtube_dl
import datetime
import random

from dotenv import load_dotenv
from apiclient.discovery import build
from lib import utils as util, paginator

#load .env file
load_dotenv()

youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': 'musics/%(id)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'geo-bypass': True,
    'verbose': False
}

ffmpeg_options = {
    'before_options': '-loglevel fatal -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

class mido_music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
        self.youtube = build("youtube", "v3", developerKey=os.environ["YOUTUBE_KEY"])

    #get_data
    async def get_data(self, ctx, key, download=False):
        loop = self.bot.loop or asyncio.get_event_loop()

        try:
            data = await loop.run_in_executor(None, functools.partial(self.ytdl.extract_info, key, download=download))
        except Exception as exc:
            raise exc

        return data

    #get_info
    async def get_info(self, ctx, url, download=False):
        data = await self.get_data(ctx, url, download)

        result = {
            "type": "Download" if download else "Stream",
            "url": data.get("url", "unknown"),
            "id": data.get("id", "unknown"),
            "webpage_url": data.get("webpage_url", "unknown"),
            "title": data.get("title", "unknown"),
            "thumbnail": data.get("thumbnail", "unknown"),
            "uploader": data.get("uploader", "unknown"),
            "uploader_url": data.get("uploader_url", "unknown"),
            "request": ctx.author.id
        }

        return result

    #shuffle
    @commands.command(name="shuffle", description="キューをシャッフルします。")
    async def shuffle(self, ctx):
        msg = await util.reply_or_send(ctx, content="> 処理中...")

        if isinstance(ctx.channel, discord.DMChannel):
            return await msg.edit(content="> DMでは使えないよ！")

        if ctx.author.voice:
            if ctx.guild.voice_client:
                if ctx.author.voice.channel == ctx.guild.voice_client.channel:
                    if self.bot.queue.get(ctx.guild.id, None):
                        for i in range(5):
                            random.shuffle(self.bot.queue[ctx.guild.id])
                        return await msg.edit(content="> シャッフルしたよ！")
                    else:
                        return await msg.edit(content="> キューが存在しないよ！")
                else:
                    return await msg.edit(content=f"> 私と同じチャンネルに接続する必要があるよ！")
            else:
                return await msg.edit(content=f"> ボイスチャンネルに接続していないため、使えないよ！")
        else:
            return await msg.edit(content=f"> ボイスチャンネルに接続してね！")

    #stop
    @commands.command(name="stop", description="音楽の再生を停止し、キューを削除してからボイスチャンネルから退出します。", aliases=["leave"])
    async def stop(self, ctx):
        msg = await util.reply_or_send(ctx, content="> 処理中...")

        if isinstance(ctx.channel, discord.DMChannel):
            return await msg.edit(content="> DMでは使えないよ！")

        if ctx.author.voice:
            if ctx.guild.voice_client:
                if ctx.author.voice.channel == ctx.guild.voice_client.channel:
                    try:
                        await ctx.guild.voice_client.disconnect()

                        try:
                            del self.bot.queue[ctx.guild.id]
                            del self.bot.loop_queue[ctx.guild.id]
                        except:
                            pass
                    except Exception as exc:
                        return await msg.edit(content=f"> エラー \n```\n{exc}\n```")
                    else:
                        await msg.edit(content=f"> 再生を停止し、ボイスチャンネルから退出しました！")
                else:
                    return await msg.edit(content=f"> 私と同じチャンネルに接続する必要があるよ！")
            else:
                return await msg.edit(content=f"> ボイスチャンネルに接続していないため、使えないよ！")
        else:
            return await msg.edit(content=f"> ボイスチャンネルに接続してね！")

    #play
    @commands.command(name="play", aliases=["p"], description="音楽を再生します。")
    async def play(self, ctx, query:str=None):
        msg = await util.reply_or_send(ctx, content="> 処理中...")

        if isinstance(ctx.channel, discord.DMChannel):
            return await msg.edit(content="> DMでは使えないよ！")

        if ctx.author.voice:
            if not ctx.guild.voice_client:
                try:
                    vc = await ctx.author.voice.channel.connect()
                except Exception as exc:
                    return await msg.edit(content=f"> エラー \n```\n{exc}\n```")
                else:
                    await msg.edit(content=f"> {vc.channel.name}に接続したよ！再生処理を行っています...")
            else:
                await msg.edit(content="> 再生処理を行っています...")
        else:
            return await msg.edit(content=f"> ボイスチャンネルに接続してね！")

        if ctx.guild.voice_client.is_paused():
            ctx.guild.voice_client.resume()
            return await msg.edit(content="> 再生を再開したよ！")

        if not query:
            await msg.edit(content="> 検索ワード/URLを送信してください。")

            try:
                message = await self.bot.wait_for("message", check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id, timeout=30.0)
            except asyncio.TimeoutError:
                return await msg.edit(content="> 30秒が経過したからキャンセルされたよ！")
            else:
                await msg.edit(content="> 再生処理を行っています....")
                query = message.content

        if query.startswith("download:"):
            try:
                data = await self.get_data(ctx, query[9:], True)
            except Exception as exc:
                return await msg.edit(content=f"> エラー \n```\n{exc}\n```")
            else:
                if data.get("_type", None) == "playlist":
                    try:
                        data = await self.get_info(ctx, f"https://youtu.be/{data['entries'][0]['id']}", True)
                    except Exception as exc:
                        return await msg.edit(content=f"> エラー \n```py\n{exc}\n```")
                    else:
                        if self.bot.queue.get(ctx.guild.id, None):
                            self.bot.queue[ctx.guild.id] = self.bot.queue[ctx.guild.id] + [data]
                            return await msg.edit(content=f"> キューに{data['title']}を追加したよ！")
                        else:
                            self.bot.queue[ctx.guild.id] = [data]
                            await msg.edit(content=f"> {data['title']}を再生するよ！")
                            self.bot.loop.create_task(self._play(ctx))
                else:
                    if self.bot.queue.get(ctx.guild.id, None):
                        self.bot.queue[ctx.guild.id] = self.bot.queue[ctx.guild.id] + [data]
                        return await msg.edit(content=f"> キューに{ret['title']}を追加したよ！")
                    else:
                        self.bot.queue[ctx.guild.id] = [data]
                        await msg.edit(content=f"> {data['title']}を再生するよ！")
                        self.bot.loop.create_task(self._play(ctx))
        else:
            try:
                data = await self.get_data(ctx, query, False)
            except Exception as exc:
                return await msg.edit(content=f"> エラー \n```\n{exc}\n```")

            lists = []

            #from sina () maybe only youtube
            if data.get("_type", None) == "playlist":
                if len(data["entries"]) >= 5:
                    lists.append(self.get_info(ctx, f"https://www.youtube.com/watch?v={data['entries'][0]['id']}", False))
                else:    
                    for i in data["entries"]:
                        lists.append(self.get_info(ctx, f"https://www.youtube.com/watch?v={i['id']}", False))

                try:
                    ret = [r for r in await asyncio.gather(*lists) if r]
                except Exception as exc:
                    return await msg.edit(content=f"> エラー \n```\n{exc}\n```")
                else:
                    if not ret:
                        return await msg.edit(content="> 再生処理中にエラーが発生しました")

                if self.bot.queue.get(ctx.guild.id, None):
                    self.bot.queue[ctx.guild.id] = self.bot.queue[ctx.guild.id] + ret
                    return await msg.edit(content=f"> キューに{len(ret)}本の動画を追加したよ！")
                else:
                    self.bot.queue[ctx.guild.id] = ret
                    await msg.edit(content=f"> プレイリストからの{len(ret)}本の動画を再生するよ！")
                    self.bot.loop.create_task(self._play(ctx))
            else:
                ret = await self.get_info(ctx, f"https://www.youtube.com/watch?v={data['id']}", False)

                if self.bot.queue.get(ctx.guild.id, None):
                    self.bot.queue[ctx.guild.id] = self.bot.queue[ctx.guild.id] + [ret]
                    return await msg.edit(content=f"> キューに{ret['title']}を追加したよ！")
                else:
                    self.bot.queue[ctx.guild.id] = [ret]
                    await msg.edit(content=f"> {ret['title']}を再生するよ！")
                    self.bot.loop.create_task(self._play(ctx))

    #skip
    @commands.command(name="skip", description="曲をスキップします。")
    async def skip(self, ctx):
        msg = await util.reply_or_send(ctx, content="> 処理中...")

        if isinstance(ctx.channel, discord.DMChannel):
            return await msg.edit(content="> DMでは使えないよ！")

        if ctx.author.voice:
            if ctx.guild.voice_client:
                if not ctx.guild.voice_client.channel == ctx.author.voice.channel:
                    return await msg.edit(content="> 私と同じチャンネルに接続している必要があるよ！")

                if ctx.guild.voice_client.is_playing():
                    loop = self.bot.loop_queue[ctx.guild.id]
                    self.bot.loop_queue[ctx.guild.id] = False
                    ctx.guild.voice_client.stop()
                    self.bot.loop_queue[ctx.guild.id] = loop
                    return await msg.edit(content="> 曲をスキップしたよ！")
                else:
                    return await msg.edit(content=f"> 再生中のみスキップできるよ！")
            else:
                return await msg.edit(content="> このサーバーでは何も再生していないよ！")
        else:
            return await msg.edit(content=f"> ボイスチャンネルに接続してね！")

    #pause
    @commands.command(name="pause", description="曲の再生を一時停止します。")
    async def pause(self, ctx):
        msg = await util.reply_or_send(ctx, content="> 処理中...")

        if isinstance(ctx.channel, discord.DMChannel):
            return await msg.edit(content="> DMでは使えないよ！")

        if ctx.author.voice:
            if ctx.guild.voice_client:
                if not ctx.guild.voice_client.channel == ctx.author.voice.channel:
                    return await msg.edit(content="> 私と同じチャンネルに接続している必要があるよ！")

                if ctx.guild.voice_client.is_playing():
                    ctx.guild.voice_client.pause()
                    return await msg.edit(content="> 曲を一時停止したよ！")
                else:
                    return await msg.edit(content=f"> 再生中のみ一時停止できるよ！")
            else:
                return await msg.edit(content="> このサーバーでは何も再生していないよ！")
        else:
            return await msg.edit(content=f"> ボイスチャンネルに接続してね！")

    #volume
    @commands.command(name="volume", aliases=["vol"], description="音量を変更します。", usage="rsp!volume <volume>")
    async def volume(self, ctx, vol: float=None):
        msg = await util.reply_or_send(ctx, content="> 処理中...")

        if isinstance(ctx.channel, discord.DMChannel):
            return await msg.edit(content="> DMでは使えないよ！")

        if ctx.author.voice:
            if ctx.guild.voice_client:
                if not ctx.guild.voice_client.channel == ctx.author.voice.channel:
                    return await msg.edit(content="> 私と同じチャンネルに接続している必要があるよ！")

                if not ctx.guild.voice_client.is_playing():
                    return await msg.edit(content="> 再生中のみ変更できるよ！")

                if not vol:
                    return await msg.edit(content="> 音量を指定してね！")

                ctx.guild.voice_client.source.volume = vol/100.0
                return await msg.edit(content=f"> 音量を{vol}にしたよ！！")
            else:
                return await msg.edit(content="> このサーバーでは何も再生していないよ！")
        else:
            return await msg.edit(content=f"> ボイスチャンネルに接続してね！")

    #nowplaying
    @commands.command(name="nowplaying", aliases=["np"], description="現在再生中の音楽を表示します。")
    async def nowplaying(self, ctx):
        msg = await util.reply_or_send(ctx, content="> 処理中...")

        if isinstance(ctx.channel, discord.DMChannel):
            return await msg.edit(content="> DMでは使えないよ！")

        if ctx.guild.voice_client:
            if ctx.guild.voice_client.is_playing():
                queue = self.bot.queue[ctx.guild.id][0]

                e = discord.Embed(title="🎶Now Playing", color=self.bot.color, timestamp=ctx.message.created_at)
                e.set_thumbnail(url=queue["thumbnail"])
                e.set_footer(text=f"Requested by {self.bot.get_user(queue['request'])}", icon_url=self.bot.get_user(queue["request"]).avatar_url_as(static_format="png"))
                e.add_field(name="再生中の曲", value=f"[{queue['title']}]({queue['webpage_url']})")
                e.add_field(name="アップロードチャンネル", value=f"[{queue['uploader']}]({queue['uploader_url']})")
                return await msg.edit(content=None, embed=e)
            else:
                return await msg.edit(content="> 現在再生中の曲はないよ！")
        else:
            return await msg.edit(content="> このサーバーでは何も再生していないよ！")

    #queue
    @commands.command(name="queue", aliases=["q"], description="キューを表示します。")
    async def queue(self, ctx):
        msg = await util.reply_or_send(ctx, content="> 処理中...")

        if isinstance(ctx.channel, discord.DMChannel):
            return await msg.edit(content="> DMでは使えないよ！")

        if not ctx.guild.voice_client:
            return await msg.edit(content="> このサーバーでは何も再生していないよ！")

        if self.bot.queue.get(ctx.guild.id, []) == []:
            return await msg.edit(content="> キューに何も追加されてないよ！")

        e = discord.Embed(title="🎶Music Queues", description="", color=self.bot.color, timestamp=ctx.message.created_at)
        count = 1
        for i in self.bot.queue[ctx.guild.id]:
            e.description += f"{count}. [{i['title']}]({i['webpage_url']})\n"
            count += 1
        return await msg.edit(content=None, embed=e)

    #loop
    @commands.command(name="loop", aliases=["repeat"], description="曲のループを切り替えます。")
    async def loop(self, ctx, loop: bool=None):
        msg = await util.reply_or_send(ctx, content="> 処理中...")

        if isinstance(ctx.channel, discord.DMChannel):
            return await msg.edit(content="> DMでは使えないよ！")

        if ctx.author.voice:
            if ctx.guild.voice_client:
                if not ctx.guild.voice_client.channel == ctx.author.voice.channel:
                    return await msg.edit(content="> 私と同じチャンネルに接続している必要があるよ！")

                if not ctx.guild.voice_client.is_playing():
                    return await msg.edit(content="> 再生中のみ変更できるよ！")

                if loop:
                    self.bot.loop_queue[ctx.guild.id] = loop
                    return await msg.edit(content=f"> ループを{loop}にしたよ！")
                else:
                    if self.bot.loop_queue[ctx.guild.id]:
                        self.bot.loop_queue[ctx.guild.id] = False
                        return await msg.edit(content=f"> ループをFalseにしたよ！")
                    else:
                        self.bot.loop_queue[ctx.guild.id] = True
                        return await msg.edit(content=f"> ループをTrueにしたよ！")
            else:
                return await msg.edit(content="> このサーバーでは何も再生していないよ！")
        else:
            return await msg.edit(content=f"> ボイスチャンネルに接続してね！")

    #delete
    @commands.command(aliases=["rm", "del"])
    async def delete(self, ctx, index: int=None):
        msg = await util.reply_or_send(ctx, content="> 処理中...")

        if isinstance(ctx.channel, discord.DMChannel):
            return await msg.edit(content="> DMでは使えないよ！")

        if not index:
            return await msg.edit(content="> 削除する曲の番号を入力してね！")

        if index <= 0:
            return await msg.edit(content="> 1以上の値を指定してね！")

        if ctx.author.voice:
            if ctx.guild.voice_client:
                if not ctx.guild.voice_client.channel == ctx.author.voice.channel:
                    return await msg.edit(content="> 私と同じチャンネルに接続している必要があるよ！")

                q = self.bot.queue.get(ctx.guild.id, None)
                if q is not None:
                    index = index - 1

                    if len(q) <= index:
                        return await msg.edit(content="> その値は指定できないよ！")

                    try:
                        del q[index]
                        return await msg.edit(content=f"> {index + 1}番目の曲を削除したよ！")
                    except Exception as exc:
                        return await msg.edit(content=f"> エラー \n```py\n{exc}\n```")
                else:
                    return await msg.edit(content="> キューが存在しないよ！")
            else:
                return await msg.edit(content="> このサーバーでは何も再生していないよ！")
        else:
            return await msg.edit(content=f"> ボイスチャンネルに接続してね！")

    #search
    @commands.command(aliases=["yt", "ytsearch"])
    async def search(self, ctx, *, query: str=None):
        msg = await util.reply_or_send(ctx, content="> 処理中...")

        if not query:
            await msg.edit(content="> 検索するワードを送信してね！")
            try:
                message = await self.bot.wait_for("message", check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id, timeout=30.0)
            except asyncio.TimeouError:
                return await msg.edit(content="> タイムアウトしました！")
            else:
                await msg.edit(content="> 検索しています...")
                query = message.content

        try:
            querys = self.youtube.search().list(part="snippet", q=query, type="video").execute()
        except Exception as exc:
            return await msg.edit(content=f"> エラー \n```\n{exc}\n```")
        else:
            items = querys.get("items", None)

            if not items:
                return await msg.edit(content="> 何も見つからなかったよ！")

            embeds = []

            for i in items:
                e = discord.Embed(title="🎶Music Search", color=self.bot.color, timestamp=ctx.message.created_at)
                e.set_thumbnail(url=i["snippet"]["thumbnails"]["medium"]["url"])
                e.add_field(name="タイトル", value=f"[{i['snippet']['title']}](https://youtube.com/watch?v={i['id']['videoId']})")
                e.add_field(name="動画URL", value=f"https://youtube.com/watch?v={i['id']['videoId']}")
                e.add_field(name="説明", value=f"```\n{i['snippet']['description']}\n```", inline=False)
                e.add_field(name="アップロード日", value=datetime.datetime.strptime(i["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y/%m/%d %H:%M:%S"))
                e.add_field(name="アップロードチャンネル", value=f"[{i['snippet']['channelTitle']}](https://youtube.com/channel/{i['snippet']['channelId']})")
                e.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url_as(static_format="png"))
                embeds.append(e)

            await msg.delete()
            page = paginator.EmbedPaginator(ctx, entries=embeds, timeout=30.0)
            await page.paginate()

    #_play
    async def _play(self, ctx, vol=0.5, src=None):
        if not self.bot.loop_queue.get(ctx.guild.id, None):
            self.bot.loop_queue[ctx.guild.id] = False

        vol = vol
        while self.bot.queue[ctx.guild.id]:
            if self.bot.queue[ctx.guild.id][0]["type"] == "Stream":
                src = discord.FFmpegPCMAudio(self.bot.queue[ctx.guild.id][0]["url"], options=ffmpeg_options)
            elif self.bot.queue[ctx.guild.id][0]["type"] == "Download":
                src = discord.FFmpegPCMAudio(f"musics/{self.bot.queue[ctx.guild.id][0]['id']}", options=ffmpeg_options)

            try:
                ctx.guild.voice_client.play(
                    discord.PCMVolumeTransformer(
                        src, 
                        volume=vol
                    )
                )
            except Exception as exc:
                self.bot.logger.warning(f"ERROR: {exc}")
                self.bot.queue[ctx.guild.id].pop(0)
            else:
                try:
                    while ctx.guild.voice_client.is_playing() or ctx.guild.voice_client.is_paused():
                        await asyncio.sleep(1)
                        vol = ctx.voice_client.source.volume
                except AttributeError:
                    pass

                if self.bot.loop_queue[ctx.guild.id]:
                    self.bot.queue[ctx.guild.id].append(self.bot.queue[ctx.guild.id][0])
                self.bot.queue[ctx.guild.id].pop(0)

def setup(bot):
    bot.add_cog(mido_music(bot))

    if not hasattr(bot, "queue"):
        bot.queue = dict()
    if not hasattr(bot, "loop_queue"):
        bot.loop_queue = dict()
