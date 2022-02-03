import discord
from discord.ext import commands

from lib import utils

class mido_help(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        
        if isinstance(bot.get_command("help"), commands.help._HelpCommandImpl):
            self.bot.remove_command("help")
    
    #generate_help
    def generate_help(self, ctx, data, *, userdb=None, command=None):
        if command:
            e = discord.Embed(title=f"Help - {command}", color=self.bot.color, timestamp=ctx.message.created_at)
            e.add_field(name=data["usage"], value=command.usage or data["none"])
            e.add_field(name=data["description"], value=data.get(f"help-{command.name}", data["none"]))
            e.add_field(name=data["aliases"], value=", ".join([f"`{row}`" for row in command.aliases]) or data["no-aliases"])
            return e
        else:
            e = discord.Embed(title=f"Help - Commands", color=self.bot.color, timestamp=ctx.message.created_at)
            if userdb is None:
                userdb = {} #override fake userdb
            
            for i in self.bot.commands:
                if ctx.author.id in self.bot.owner_ids or userdb.get("rank", 0) >= 2:
                    e.add_field(name=i.name, value=data.get(f"help-{i.name}", data["none"]))
                else:
                    if not isinstance(i.cog, type(self.bot.cogs["mido_admins"])):
                        if not "jishaku" in i.name:
                            e.add_field(name=i.name, value=data.get(f"help-{i.name}", data["none"]))
            
            return e
    
    #help
    @commands.command(usage="help [command]")
    async def help(self, ctx, command: str=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)        
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")

        userdb = None #init local userdb
        try:
            userdb = await self.bot.db.fetchone(
                "SELECT * FROM users WHERE user_id=%s", 
                (ctx.author.id,)
            )
        except:
            userdb = None
        
        if not command:
            return await m.edit(content=None, embed=self.generate_help(ctx, d, userdb=userdb))
        else:
            command = self.bot.get_command(command)
            if not command:
                return await m.edit(content=None, embed=self.generate_help(ctx, d, userdb=userdb))
            return await m.edit(content=None, embed=self.generate_help(ctx, d, command=command))

def setup(bot):
    bot.add_cog(mido_help(bot))
