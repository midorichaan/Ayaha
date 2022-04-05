import discord
from discord.ext import commands

import asyncio
from lib import utils

class mido_guild_settings(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    #check_db
    async def check_db(self):
        try:
            await self.bot.db.execute(
                "SELECT 1"
            )
        except:
            return False
        return True

    #build_gs_embed
    async def build_gs_embed(self, ctx, type: int, db, *, lang: str=None, value: str=None):
        if not lang:
            lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        if type == 1:
            e = discord.Embed(
                title=d["guildsettings-prefix"], 
                description=d["guildsettings-type-prefix"],
                color=self.bot.color,
                timestamp=ctx.message.created_at
            )
            return e
        elif type == 2:
            e = discord.Embed(
                title=d["guildsettings-ticket-settings"], 
                description="",
                color=self.bot.color,
                timestamp=ctx.message.created_at
            )

            val = [
                "❗: {} ({})\n".format(d["guildsettings-ticket-adminmention"], d["guildsettings-true"] if db["admin_role_mention"] else d["guildsettings-false"]),
                "📢: {} ({})\n".format(d["guildsettings-ticket-mention_role"], ctx.guild.get_role(db.get("admin_role_id", 0)).mention if db["admin_role_id"] else d["guildsettings-false"]),
                "📄: {} ({})\n".format(d["guildsettings-ticket-opencategory"], ctx.guild.get_channel(db["open_category_id"]) if db["open_category_id"] else d["guildsettings-false"]),
                "📑: {} ({})\n".format(d["guildsettings-ticket-closecategory"], ctx.guild.get_channel(db["close_category_id"]) if db["close_category_id"] else d["guildsettings-false"]),
                "🗑: {} ({})\n".format(d["guildsettings-ticket-deleteticket"], d["guildsettings-true"] if db["delete_after_closed"] else d["guildsettings-false"]),
                "📩: {} ({})\n".format(d["guildsettings-ticket-moveclosed"], d["guildsettings-true"] if db["move_after_closed"] else d["guildsettings-false"]),
                "📝: {} ({})\n".format(d["guildsettings-ticket-paneltitle"], db["ticket_panel_title"] if db["ticket_panel_title"] else d["none"]),
                "📖: {} ({})\n".format(d["guildsettings-ticket-paneldescription"], db["ticket_panel_description"] if db["ticket_panel_description"] else d["none"]),
                "❌: {}".format(d["cancel"])
            ]

            for i in val:
                e.description += i

            return e
        else:
            e = discord.Embed(
                title=d["guildsettings"], 
                description="",
                color=self.bot.color,
                timestamp=ctx.message.created_at
            )

            settings = [
                "📝: {} ({})\n".format(d["guildsettings-prefix"], db["prefix"] or d["guildsettings-no-prefix"]),
                "📚: {} ({})\n".format(d["guildsettings-toggle-baseprefix"], d["guildsettings-false"] if db["disable_base_prefix"] else d["guildsettings-true"]),
                "✉: {}\n".format(d["guildsettings-ticket-settings"]),
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

    #delete_message
    async def delete_message(self, message):
        try:
            await message.delete()
        except:
            pass

    #ticket_config
    async def ticket_config(self, ctx, message, lang):
        while True:
            try:
                r, u = await self.bot.wait_for("reaction_add", check=lambda r, u: u.id == ctx.author.id and r.message.id == message.id, timeout=30.0)
            except asyncio.TimeoutError:
                await self.clear_reactions(ctx, message)
                break
            else:
                if str(r) in ["❗", "📢", "📄", "📑", "🗑", "📩", "📝", "📖", "❌"]:
                    if ctx.channel.permissions_for(ctx.me).manage_messages:
                        await message.remove_reaction(str(r), ctx.author)

                data = await self.bot.langutil.get_lang(lang)
                db = await self.bot.db.fetchone(
                    "SELECT * FROM ticketconfig WHERE guild_id=%s",
                    (ctx.guild.id,)
                )
                if not db:
                    break

                if r.emoji == "❗":
                    if db["admin_role_mention"]:
                        await self.bot.db.execute(
                            "UPDATE ticketconfig SET admin_role_mention=%s WHERE guild_id=%s",
                            (0, ctx.guild.id)
                        )
                    else:
                        await self.bot.db.execute(
                            "UPDATE ticketconfig SET admin_role_mention=%s WHERE guild_id=%s",
                            (1, ctx.guild.id)
                        )

                    db = await self.bot.db.fetchone(
                        "SELECT * FROM ticketconfig WHERE guild_id=%s",
                        (ctx.guild.id,)
                    )
                    gs = await self.build_gs_embed(
                        ctx,
                        2,
                        db,
                        lang=lang
                    )
                    await message.edit(embed=gs)
                elif r.emoji == "📢":
                    try:
                        i = await utils.reply_or_send(
                            message,
                            content=f"> {data['wait-for-reply']}"
                        )

                        check = lambda x: x.author.id == ctx.author.id and x.channel.id == ctx.channel.id and x.content.isdigit()
                        m = await self.bot.wait_for(
                            "message",
                            check=check,
                            timeout=15.0
                        )
                    except Exception as exc:
                        self.bot.logger.warning(f"ERROR: {exc}")
                    else:
                        await i.delete()
                        await self.delete_message(m)
                        await self.bot.db.execute(
                            "UPDATE ticketconfig SET admin_role_id=%s WHERE guild_id=%s",
                            (m.content, ctx.guild.id)
                        )

                        db = await self.bot.db.fetchone(
                            "SELECT * FROM ticketconfig WHERE guild_id=%s",
                            (ctx.guild.id,)
                        )
                        gs = await self.build_gs_embed(
                            ctx,
                            2,
                            db,
                            lang=lang
                        )
                        await message.edit(embed=gs)
                elif r.emoji == "📄":
                    try:
                        i = await utils.reply_or_send(
                            message,
                            content=f"> {data['wait-for-reply']}"
                        )

                        check = lambda x: x.author.id == ctx.author.id and x.channel.id == ctx.channel.id and x.content.isdigit()
                        m = await self.bot.wait_for(
                            "message",
                            check=check,
                            timeout=15.0
                        )
                    except Exception as exc:
                        self.bot.logger.warning(f"ERROR: {exc}")
                    else:
                        await i.delete()
                        await self.delete_message(m)
                        await self.bot.db.execute(
                            "UPDATE ticketconfig SET open_category_id=%s WHERE guild_id=%s",
                            (m.content, ctx.guild.id)
                        )

                    db = await self.bot.db.fetchone(
                        "SELECT * FROM ticketconfig WHERE guild_id=%s",
                        (ctx.guild.id,)
                    )
                    gs = await self.build_gs_embed(
                        ctx,
                        2,
                        db,
                        lang=lang
                    )
                    await message.edit(embed=gs)
                elif r.emoji == "📑":
                    try:
                        i = await utils.reply_or_send(
                            message,
                            content=f"> {data['wait-for-reply']}"
                        )

                        check = lambda x: x.author.id == ctx.author.id and x.channel.id == ctx.channel.id and x.content.isdigit()
                        m = await self.bot.wait_for(
                            "message",
                            check=check,
                            timeout=15.0
                        )
                    except Exception as exc:
                        self.bot.logger.warning(f"ERROR: {exc}")
                    else:
                        await i.delete()
                        await self.delete_message(m)
                        await self.bot.db.execute(
                            "UPDATE ticketconfig SET close_category_id=%s WHERE guild_id=%s",
                            (m.content, ctx.guild.id)
                        )

                    db = await self.bot.db.fetchone(
                        "SELECT * FROM ticketconfig WHERE guild_id=%s",
                        (ctx.guild.id,)
                    )
                    gs = await self.build_gs_embed(
                        ctx,
                        2,
                        db,
                        lang=lang
                    )
                    await message.edit(embed=gs)
                elif r.emoji == "🗑":
                    if db["delete_after_closed"]:
                        await self.bot.db.execute(
                            "UPDATE ticketconfig SET delete_after_closed=%s WHERE guild_id=%s",
                            (0, ctx.guild.id)
                        )
                    else:
                        await self.bot.db.execute(
                            "UPDATE ticketconfig SET delete_after_closed=%s WHERE guild_id=%s",
                            (1, ctx.guild.id)
                        )

                    db = await self.bot.db.fetchone(
                        "SELECT * FROM ticketconfig WHERE guild_id=%s",
                        (ctx.guild.id,)
                    )
                    gs = await self.build_gs_embed(
                        ctx,
                        2,
                        db,
                        lang=lang
                    )
                    await message.edit(embed=gs)
                elif r.emoji == "📩":
                    if db["move_after_closed"]:
                        await self.bot.db.execute(
                            "UPDATE ticketconfig SET move_after_closed=%s WHERE guild_id=%s",
                            (0, ctx.guild.id)
                        )
                    else:
                        await self.bot.db.execute(
                            "UPDATE ticketconfig SET move_after_closed=%s WHERE guild_id=%s",
                            (1, ctx.guild.id)
                        )

                    db = await self.bot.db.fetchone(
                        "SELECT * FROM ticketconfig WHERE guild_id=%s",
                        (ctx.guild.id,)
                    )
                    gs = await self.build_gs_embed(
                        ctx,
                        2,
                        db,
                        lang=lang
                    )
                    await message.edit(embed=gs)
                elif r.emoji == "📝":
                    try:
                        i = await utils.reply_or_send(
                            message,
                            content=f"> {data['wait-for-reply']}"
                        )

                        check = lambda x: x.author.id == ctx.author.id and x.channel.id == ctx.channel.id
                        m = await self.bot.wait_for(
                            "message",
                            check=check,
                            timeout=15.0
                        )
                    except Exception as exc:
                        self.bot.logger.warning(f"ERROR: {exc}")  
                    else:
                        await i.delete()
                        await self.delete_message(m)
                        await self.bot.db.execute(
                            "UPDATE ticketconfig SET ticket_panel_title=%s WHERE guild_id=%s",
                            (m.content, ctx.guild.id)
                        )

                    db = await self.bot.db.fetchone(
                        "SELECT * FROM ticketconfig WHERE guild_id=%s",
                        (ctx.guild.id,)
                    )
                    gs = await self.build_gs_embed(
                        ctx,
                        2,
                        db,
                        lang=lang
                    )
                    await message.edit(embed=gs)
                elif r.emoji == "📖":
                    try:
                        i = await utils.reply_or_send(
                            message,
                            content=f"> {data['wait-for-reply']}"
                        )

                        check = lambda x: x.author.id == ctx.author.id and x.channel.id == ctx.channel.id
                        m = await self.bot.wait_for(
                            "message",
                            check=check,
                            timeout=15.0
                        )
                    except Exception as exc:
                        self.bot.logger.warning(f"ERROR: {exc}")
                    else:
                        await i.delete()
                        await self.delete_message(m)
                        await self.bot.db.execute(
                            "UPDATE ticketconfig SET ticket_panel_description=%s WHERE guild_id=%s",
                            (m.content, ctx.guild.id)
                        )

                    db = await self.bot.db.fetchone(
                        "SELECT * FROM ticketconfig WHERE guild_id=%s",
                        (ctx.guild.id,)
                    )
                    gs = await self.build_gs_embed(
                        ctx,
                        2,
                        db,
                        lang=lang
                    )
                    await message.edit(embed=gs)
                elif r.emoji == "❌":
                    break

    #guildsettings
    @commands.command(name="guildsettings", aliases=["guildsetting", "gs", "config"], usage="guildsettings")
    @commands.guild_only()
    @commands.bot_has_permissions(add_reactions=True, embed_links=True)
    @commands.has_permissions(manage_guild=True)
    async def guildsettings(self, ctx):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")

        dbchecker = await self.check_db()
        if not dbchecker:
            return await m.edit(content=f"> {d['exc-cant_fetch-data']}")

        gs = await self.bot.db.fetchone("SELECT * FROM guilds WHERE guild_id=%s", (ctx.guild.id,))
        await m.edit(content=None, embed=await self.build_gs_embed(ctx, 0, gs, lang=lang))
        await m.add_reaction("📝")
        await m.add_reaction("📚")
        await m.add_reaction("✉")
        await m.add_reaction("❌")

        while True:
            try:
                r, u = await self.bot.wait_for("reaction_add", check=lambda r, u: u.id == ctx.author.id and r.message.id == m.id, timeout=30.0)
            except asyncio.TimeoutError:
                await self.clear_reactions(ctx, m)
                await m.reply(f"> {d['timeout']}")
                break
            else:
                if ctx.channel.permissions_for(ctx.me).manage_messages:
                    await m.remove_reaction(str(r), ctx.author)

                if r.emoji == "📝":
                    await self.clear_reactions(ctx, m)
                    await m.edit(embed=await self.build_gs_embed(ctx, 1, gs))

                    msg = await self.bot.wait_for("message", check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id)
                    await msg.delete()

                    if msg.content == "reset":
                        await self.bot.db.execute("UPDATE guilds SET prefix=%s WHERE guild_id=%s", (None, ctx.guild.id))
                    else:
                        await self.bot.db.execute("UPDATE guilds SET prefix=%s WHERE guild_id=%s", (msg.content, ctx.guild.id))
                    gs = await self.bot.db.fetchone("SELECT * FROM guilds WHERE guild_id=%s", (ctx.guild.id,))
                    await m.edit(content=None, embed=await self.build_gs_embed(ctx, 0, gs))
                    await m.add_reaction("📝")
                    await m.add_reaction("📚")
                    await m.add_reaction("✉")
                    await m.add_reaction("❌")
                elif r.emoji == "📚":
                    await self.clear_reactions(ctx, m)
                    await m.edit(embed=await self.build_gs_embed(ctx, 0, gs))

                    if gs["disable_base_prefix"]:
                        await self.bot.db.execute("UPDATE guilds SET disable_base_prefix=%s WHERE guild_id=%s", (0, ctx.guild.id,))
                    else:
                        await self.bot.db.execute("UPDATE guilds SET disable_base_prefix=%s WHERE guild_id=%s", (1, ctx.guild.id,))

                    gs = await self.bot.db.fetchone("SELECT * FROM guilds WHERE guild_id=%s", (ctx.guild.id,))
                    await m.edit(content=None, embed=await self.build_gs_embed(ctx, 0, gs))
                    await m.add_reaction("📝")
                    await m.add_reaction("📚")
                    await m.add_reaction("✉")
                    await m.add_reaction("❌")
                elif r.emoji == "✉":
                    await self.clear_reactions(ctx, m)
                    db = await self.bot.db.fetchone("SELECT * FROM ticketconfig WHERE guild_id=%s", (ctx.guild.id,))
                    await m.edit(embed=await self.build_gs_embed(ctx, 2, db))

                    emojis = ["❗", "📢", "📄", "📑", "🗑", "📩", "📝", "📖", "❌"]
                    for i in emojis:
                        await m.add_reaction(i)

                    await self.ticket_config(ctx, m, lang)

                    await self.clear_reactions(ctx, m)
                    gs = await self.bot.db.fetchone("SELECT * FROM guilds WHERE guild_id=%s", (ctx.guild.id,))
                    await m.edit(content=None, embed=await self.build_gs_embed(ctx, 0, gs))
                    await m.add_reaction("📝")
                    await m.add_reaction("📚")
                    await m.add_reaction("✉")
                    await m.add_reaction("❌")
                elif r.emoji == "❌":
                    await self.clear_reactions(ctx, m)
                    break

def setup(bot):
    bot.add_cog(mido_guild_settings(bot))
