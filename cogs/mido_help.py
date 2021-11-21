import discord
from discord.ext import commands

from lib import utils

class mido_help(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        
        if isinstance(bot.get_command("help"), commands.help._HelpCommandImpl):
            self.bot.remove_command("help")
    
    #generate_help
    def generate_help(self, ctx, data, *, command=None):
        if command:
            e = discord.Embed(title=f"Help - {command}", color=self.bot.color, timestamp=ctx.message.created_at)
            e.add_field(name=data["usage"], value=command.usage)
            e.add_field(name=data["description"], value=d[f"cmd-{command}"])
            e.add_field(name=data["aliases"], value=", ".join([f"`{row}`" for row in command.aliases]))
            return e
        else:
            e = discord.Embed(title=f"Help - Commands", color=self.bot.color, timestamp=ctx.message.created_at)
            
            for i in self.bot.commands:
                e.add_field(name=i.name, value=d[f"cmd-{i.name}"])
            
            return e
    
    #help
    @commands.command(usage="help [command]")
    async def help(self, ctx, command: str=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")
        
        if not command:
            return await m.edit(content=None, embed=self.generate_help(ctx, d))
        else:
            command = self.bot.get_command(command)
            if not command:
                return await m.edit(content=None, embed=self.generate_help(ctx, d))
            return await m.edit(content=None, embed=self.generate_help(ctx, d, command=command))

def setup(bot):
    bot.add_cog(mido_help(bot))
