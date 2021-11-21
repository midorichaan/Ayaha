import discord
from discord.ext import commands

import asyncio
from lib import utils

class mido_guild_settings(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    
    #build_gs_embed
    async def build_gs_embed(self, ctx, type: int, db, *, lang: str=None, value: str=None):
        if not lang:
            lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        if type == 1:
            e = discord.Embed(title=d["guildsettings-prefix"], 
                              description=d["guildsettings-set-prefix"].replace("{REPLACE}", value or d["none"]),
                              color=self.bot.color,
                              timestamp=ctx.message.created_at
                             )
            return e
        elif type == 2:
            e = discord.Embed(title=d["guildsettings-toggle-base-prefix"], 
                              description=d["guildsettings-toggled-baseprefix"].replace("{REPLACE}", value),
                              color=self.bot.color,
                              timestamp=ctx.message.created_at
                             )
            return e
        else:
            e = discord.Embed(title=d["guildsettings"], 
                              description="",
                              color=self.bot.color,
                              timestamp=ctx.message.created_at
                             )
            
            settings = [
                "📝: {} ({})\n".format(d["guildsettings-prefix"], db["prefix"] or d["guildsettings-no-prefix"]),
                "📚: {} ({})\n".format(d["guildsettings-toggle-baseprefix"], d["guildsettings-true"]) if db["disable_base_prefix"] else d["guildsettings-false"],
                "❌: {}".format(d["cancel"])
            ]
        
            for i in settings:
                e.description += i
        
            return e
    
    #clear_reactions
    async def clear_reactions(self, ctx, msg):
        if ctx.channel.permissions_for(ctx.me).manage_messages:
            await msg.clear_reactions()
        else:
            asyncio.gather(*[msg.remove_reaction(str(r), ctx.author) for r in msg.reactions()])
    
    #guildsettings
    @commands.command(name="guildsettings", aliases=["guildsetting", "gs", "config"], usage="guildsettings")
    @commands.bot_has_permissions(add_reactions=True, embed_links=True, manage_guild=True)
    async def guildsettings(self, ctx):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        
        gs = await self.bot.db.fetchone("SELECT * FROM guilds WHERE guild_id=%s", (ctx.guild.id,))
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")
        await m.edit(content=None, embed=await self.build_gs_embed(ctx, 0, gs, lang=lang))
        await m.add_reaction("📝")
        await m.add_reaction("📚")
        await m.add_reaction("❌")
        
        while True:
            try:
                r, u = await self.bot.wait_for("reaction_add", check=lambda r, u: u.id == ctx.author.id and r.message.id == m.id, timeout=30.0)
            except asyncio.TimeoutError:
                await self.clear_reactions(ctx, m)
                await m.edit(content=f"> {d['timeout']}")
                break
            else:
                if ctx.channel.permissions_for(ctx.me).manage_messages:
                    await m.remove_reaction(str(r), ctx.author)
                
                if r.emoji == "📝":
                    await self.clear_reactions(ctx, m)
                    await m.edit(embed=await self.build_gs_embed(ctx, 1, db))
                
                    msg = await self.bot.wait_for("message", check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id)
                    await msg.delete()
                    
                    await self.bot.db.execute("UPDATE guilds SET prefix=%s WHERE guild_id=%s", (msg.content, ctx.guild.id))
                    await m.edit(content=None, embed=await self.build_gs_embed(ctx, 0, db, value=msg.content))
                    await m.add_reaction("📝")
                    await m.add_reaction("📚")
                    await m.add_reaction("❌")
                elif r.emoji == "📚":
                    await self.clear_reactions(ctx, m)
                    await m.edit(embed=await self.build_gs_embed(ctx, 2, db))
                    v = 0
                    
                    if gs["disable_base_prefix"]:
                        await self.bot.db.execute("UPDATE guilds SET disable_base_prefix=%s WHERE guild_id=%s", (0, ctx.guild.id,))
                    else:
                        await self.bot.db.execute("UPDATE guilds SET disable_base_prefix=%s WHERE guild_id=%s", (1, ctx.guild.id,))
                        v = 1
                    await asyncio.sleep(3)
                    
                    await m.edit(content=None, embed=await self.build_gs_embed(ctx, 0, db, value=v))
                    await m.add_reaction("📝")
                    await m.add_reaction("📚")
                    await m.add_reaction("❌")
                elif r.emoji == "❌":
                    await self.clear_reactions(ctx, m)
                    break

def setup(bot):
    bot.add_cog(mido_guild_settings(bot))
