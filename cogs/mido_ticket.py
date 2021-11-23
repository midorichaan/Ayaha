import discord
from discord.ext import commands

from lib import utils, ticketutil

class mido_ticket(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.ticketutil = ticketutil.TicketUtil(bot)
    
    #generate_help
    def generate_help(self, ctx, data, *, command=None):
        if command:
            e = discord.Embed(title=f"Help - {command.name}", color=self.bot.color, timestamp=ctx.message.created_at)
            e.add_field(name=data["usage"], value=command.usage)
            e.add_field(name=data["description"], value=data[f"help-{command.name}"])
            e.add_field(name=data["aliases"], value=", ".join([f"`{row}`" for row in command.aliases]) or data["no-aliases"])
            return e
        else:
            e = discord.Embed(title=f"Help - ticket", color=self.bot.color, timestamp=ctx.message.created_at)
            
            for i in self.bot.get_command("ticket").commands:
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
                return await m.edit(content=None, embed=self.generate_help(ctx, d, command=c))
            return await m.edit(content=None, embed=self.generate_help(ctx, d))
        else:
            return await m.edit(content=None, embed=self.generate_help(ctx, d))
    
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
            msg = d['ticket-panel-created'].replace("{PANEL_URL}", panel_obj.jump_url)
            return await m.edit(content=f"> {msg}")
    
    #panel
    @panel.command(usage="delete [channel]")
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
            p = await commands.MessageConverter().convert(ctx, f"{exists['channel_id']}-{exists['panel_id']}"))
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
    
def setup(bot):
    bot.add_cog(mido_ticket(bot))
