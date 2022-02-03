import discord
from discord.ext import commands

from lib import utils, ticketutil

class mido_ticket(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.ticketutil = ticketutil.TicketUtil(bot)
        self.enabled = True
        asyncio.gather(check_db())

    #check_db
    async def check_db(self):
        try:
            await self.bot.db.execute(
                "SELECT 1"
            )
        except:
            self.enabled = False
            print("[Error] failed to connect database")
            print("[System] unloading cogs.mido_ticket")

            try:
                self.bot.unload_cog(self)
            except Exception as exc:
                print(f"[Error] failed to unload cog → {exc}")
        else:
            self.enabled = True
            print("[System] Successfully connected database")
    
    #raw_reaction
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        pass
    
    #on_msg
    @commands.Cog.listener()
    async def on_message(self, msg):
        db = await self.ticketutil.get_ticket(msg.channel.id)
        if db:
            if db["status"] == 2:
                if not msg.author.id == int(db["author_id"]):
                    return
                
                ctx = await self.bot.get_context(msg)
                lang = await self.bot.langutil.get_user_lang(ctx.author.id)
                d = await self.bot.langutil.get_lang(lang)
                
                try:
                    panel = await commands.MessageConverter().convert(ctx, f"{msg.channel.id}-{db['panel_id']}")
                except Exception as exc:
                    print(f"[Error] {exc}")
                    return await utils.reply_or_send(ctx, content=f"> {d['ticket-cant-fetch-panel']}")
                else:
                    e = panel.embeds[0]
                    e.set_field_at(0, name="チケット作成理由 / Reason", value=f"```\n{msg.content}\n```", inline=False)
                    e.set_field_at(1, name="ステータス / Status", value=f"```\nオープン / Open\n```", inline=False)
                    await panel.edit(embed=e)
                    await self.ticketutil.edit_reason(msg.channel.id, reason=msg.content)
    
    #generate_help
    def generate_help(self, ctx, data, *, command=None, gen_cmd=None):
        if command:
            e = discord.Embed(title=f"Help - {command.name}", color=self.bot.color, timestamp=ctx.message.created_at)
            e.add_field(name=data["usage"], value=command.usage)
            e.add_field(name=data["description"], value=data[f"help-{command.name}"])
            e.add_field(name=data["aliases"], value=", ".join([f"`{row}`" for row in command.aliases]) or data["no-aliases"])
            return e
        else:
            e = discord.Embed(title=f"Help - ticket", color=self.bot.color, timestamp=ctx.message.created_at)
            
            for i in self.bot.get_command(gen_cmd).commands:
                e.add_field(name=i.name, value=data[f"help-{i.name}"])
            
            return e
    
    #try_delete
    async def try_delete(self, msg):
        try:
            await msg.delete()
        except:
            pass
    
    #ticket
    @commands.group(usage="ticket [args]", invoke_without_command=True)
    async def ticket(self, ctx):
        pass
    
    #help
    @ticket.command(name="help", usage="help [cmd]")
    @commands.guild_only()
    async def help(self, ctx, cmd=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")
        
        if cmd:
            c = self.bot.get_command("ticket").get_command(cmd)
            if c:
                return await m.edit(content=None, embed=self.generate_help(ctx, d, command=c, gen_cmd="ticket"))
            return await m.edit(content=None, embed=self.generate_help(ctx, d, gen_cmd="ticket"))
        else:
            return await m.edit(content=None, embed=self.generate_help(ctx, d, gen_cmd="ticket"))
    
    #config
    @ticket.command(usage="config")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def config(self, ctx):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")
        return await m.edit(content=f"> {d['ticket-use-guildsetting']}")
    
    #panel
    @ticket.group(usage="panel <args>")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def panel(self, ctx):
        pass
    
    #panel
    @panel.command(name="help", usage="help")
    @commands.guild_only()
    async def panel_help(self, ctx):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")
        return await m.edit(content=None, embed=self.generate_help(ctx, d, gen_cmd="ticket panel"))
    
    #panel
    @panel.command(usage="create [channel]")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def create(self, ctx, channel=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")
        
        if channel:
            try:
                channel = await commands.TextChannelConverter().convert(ctx, str(channel))
            except:
                return await m.edit(content=f"> {d['channel-not-exists']}")
        else:
            channel = ctx.channel
        
        try:
            panel = await self.ticketutil.create_panel(guild_id=ctx.guild.id)
        except:
            return await m.edit(content=f"> {d['ticket-unknown-exc']}")
        else:
            panel_obj = await channel.send(embed=panel)
            await self.ticketutil.register_panel(
                panel_id=panel_obj.id, guild_id=ctx.guild.id, channel_id=channel.id, author_id=ctx.author.id, created_at=str(panel_obj.created_at)
            )
            await panel_obj.add_reaction("📩")
            msg = d['ticket-panel-created'].replace("{PANEL_URL}", panel_obj.jump_url)
            return await m.edit(content=f"> {msg}")
    
    #panel
    @panel.command(usage="delete [panel_id]")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def delete(self, ctx, panel_id=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")
        
        if not panel_id:
            return await m.edit(content=f"> {d['args-required']}")
        
        exists = await self.ticketutil.panel_exists(panel_id=panel_id)
        if not exists:
            return await m.edit(content=f"> {d['ticket-panel-notexists']}")
        
        try:
            p = await commands.MessageConverter().convert(ctx, f"{exists['channel_id']}-{exists['panel_id']}")
        except:
            pass
        finally:       
            try:
                panel = await self.ticketutil.delete_panel(panel_id)
                await self.try_delete(p)
            except:
                return await m.edit(content=f"> {d['ticket-unknown-exc']}")
            else:
                return await m.edit(content=f"> {d['ticket-panel-deleted']}")
    
    #panel
    @panel.command(usage="refresh [panel_id]", aliases=["ref"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def refresh(self, ctx, panel_id=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")
        
        if not panel_id:
            return await m.edit(content=f"> {d['args-required']}")
        
        exists = await self.ticketutil.panel_exists(panel_id=panel_id)
        if not exists:
            return await m.edit(content=f"> {d['ticket-panel-notexists']}")
        
        try:
            msg = await commands.MessageConverter().convert(ctx, f"{exists['channel_id']}-{exists['panel_id']}")
        except:
            return await m.edit(content=f"> {d['ticket-panel-notfound']}")
        else:
            embed = await self.ticketutil.create_panel(guild_id=ctx.guild.id)
            await msg.edit(embed=embed)
            await m.edit(content=f"> {d['ticket-panel-refreshed']}")
    
    #create
    @ticket.command(usage="create [reason]")
    @commands.guild_only()
    async def create(self, ctx, *, reason: str=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")
        
        tickets = [i for i in ctx.guild.channels if str(ctx.author.id) in str(i)]
        ow = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(
                manage_channels=True, 
                manage_messages=True, 
                embed_links=True, 
                attach_files=True, 
                read_message_history=True,
                external_emojis=True,
                use_external_emojis=True
            )
        }
        ch = None
        status = 0
        config = await self.ticketutil.get_config(ctx.guild.id)
        if config["open_category_id"]:
            try:
                ch = await ctx.guild.get_channel(config["open_category_id"]).create_text_channel(
                    name=f"ticket-{ctx.author.id}-{len(tickets) + 1}",
                    overwrites=ow,
                    reason=f"Ticket channel created by {ctx.author} (ID: {ctx.author.id})"
                )
            except Exception as exc:
                print(f"[Error] {exc}")
                return await m.edit(content=f"> {d['ticket-cant-create']}")
        else:
            try:
                ch = await ctx.guild.create_text_channel(
                    name=f"ticket-{ctx.author.id}-{len(tickets) + 1}",
                    overwrites=ow,
                    reason=f"Ticket channel created by {ctx.author} (ID: {ctx.author.id})"
                )
            except Exception as exc:
                print(f"[Error] {exc}")
                return await m.edit(content=f"> {d['ticket-cant-create']}")
            
        e = discord.Embed(
                title=f"Ticket - {ctx.author}",
                color=self.bot.color
            )
        
        if not reason:
            status = 2
            e.add_field(name="チケット作成理由 / Reason", value=f"```\nnone\n```", inline=False)
            e.add_field(name="ステータス / Status", value=f"```\n理由待ち / Wait for reason\n```", inline=False)
        else:
            status = 1
            e.add_field(name="チケット作成理由 / Reason", value=f"```\n{reason}\n```", inline=False)
            e.add_field(name="ステータス / Status", value=f"```\nオープン / Open\n```", inline=False)
        panel = await ch.send(embed=e)
        await panel.add_reaction("🔒")
        
        await self.ticketutil.create_ticket(
            ctx.guild.id,
            panel.id,
            ctx.author.id,
            ch.id,
            status=status,
            reason=reason
        )
        
        await m.edit(content=f"> {d['ticket-created']} \n→ {ch.mention}")
    
    #close
    @ticket.command(usage="close <ticket>")
    @commands.guild_only()
    async def close(self, ctx, ticket: commands.TextChannelConverter=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")
        
        if not ticket:
            ticket = ctx.channel
        
        ow = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(send_messages=False, add_reactions=False),
            ctx.guild.me: discord.PermissionOverwrite(
                manage_channels=True, 
                manage_messages=True, 
                embed_links=True, 
                attach_files=True, 
                read_message_history=True,
                external_emojis=True,
                use_external_emojis=True
            )
        }
        
        ticketch = ticket
        ticketdb = await self.ticketutil.get_ticket(ticket.id)
        if not ticketdb:
            return await m.edit(content=f"> {d['ticket-notfound']}")
        
        await self.ticketutil.close_ticket(ticketch.id)
        try:
            panel = await commands.MessageConverter().convert(ctx, f"{ticketch.id}-{ticketdb['panel_id']}")
        except Exception as exc:
            print(f"[Error] {exc}")
        else:
            e = panel.embeds[0]
            e.set_field_at(1, name="ステータス / Status", value=f"```\nクローズ / Close\n```", inline=False)
            await panel.edit(embed=e)
        
        config = await self.ticketutil.get_config(ctx.guild.id)
        if config["delete_after_closed"]:
            await m.edit(content=f"> {d['ticket-delete-after']}")
            await asyncio.sleep(5)
            return await ticketch.delete()

        if config["move_after_closed"]:
            if config.get("close_category_id", None):
                await m.edit(content=f"> {d['ticket-closed']}")
                await ticketch.edit(
                    name=ticketch.name.replace("ticket", "close"),
                    category=ctx.guild.get_channel(config["close_category_id"]),
                    overwrites=ow
                )
                return await m.edit(content=f"> {d['ticket-closed']}")
        
        await ticketch.edit(
            name=ticketch.name.replace("ticket", "close"),
            overwrites=ow,
        )
        await m.edit(content=f"> {d['ticket-closed']}")
        
def setup(bot):
    bot.add_cog(mido_ticket(bot))
