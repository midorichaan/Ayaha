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
    @commands.has_permission(manage_guild=True)
    async def panel(self, ctx):
        pass
    
    #panel
    @panel.command(usage="create [channel]")
    @commands.guild_only()
    @commands.has_permission(manage_guild=True)
    async def panel(self, ctx, channel=None):
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
            msg = d['ticket-panel-created'].replace("{PANEL_URL}", panel_obj.jump_url)
            return await m.edit(content=f"> {msg}")
    
def setup(bot):
    bot.add_cog(mido_ticket(bot))
