import discord
from discord.ext import commands

import asyncio
import io
import os
import textwrap
import traceback
import sys
from contextlib import redirect_stdout
from lib import utils

class mido_admins(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self._ = None
        self.success = "✅"
        self.failed = "❌"
    
    #generate_help
    def generate_help(self, ctx, data, *, command=None):
        if command:
            e = discord.Embed(title=f"Help - {command.name}", color=self.bot.color, timestamp=ctx.message.created_at)
            e.add_field(name=data["usage"], value=command.usage)
            e.add_field(name=data["description"], value=data[f"help-{command.name}"])
            e.add_field(name=data["aliases"], value=", ".join([f"`{row}`" for row in command.aliases]) or data["no-aliases"])
            return e
        else:
            e = discord.Embed(title=f"Help - system", color=self.bot.color, timestamp=ctx.message.created_at)
            
            for i in self.bot.get_command("system").commands:
                e.add_field(name=i.name, value=data[f"help-{i.name}"])
            
            return e
    
    #eval
    @commands.is_owner()
    @commands.command(name="eval", usage="eval <code>")
    async def _eval(self, ctx, *, code: str=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        
        if not code:
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"> {d['args-required']}")
        
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'self': self,
            '_': self._
        }
        
        env.update(globals())
        
        code = utils.cleanup_code(code)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(code, "  ")}'
        
        try:
            exec(to_compile, env)
        except Exception as exc:
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"```py\n{exc.__class__.__name__}: {exc}\n```")
        
        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as exc:
            await ctx.message.add_reaction(self.failed)
            value = stdout.getvalue()
            return await utils.reply_or_send(ctx, content=f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            await ctx.message.add_reaction(self.success)

            if ret is None:
                if value:
                    await utils.reply_or_send(ctx, content=f'```py\n{value}\n```')
            else:
                self._ = ret
                await utils.reply_or_send(ctx, content=f'```py\n{value}{ret}\n```')
    
    #sql
    @commands.is_owner()
    @commands.command(name="sql", usage="sql <command>")
    async def sql(self, ctx, *, sql=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        
        if not sql:
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"> {d['args-required']}")
       
        ret = await self.bot.db.fetchall(sql)
        
        try:
            await ctx.message.add_reaction(self.success)
            return await utils.reply_or_send(ctx, content=ret)   
        except Exception as exc:
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"```py\n{exc}\n```")
    
    #shell
    @commands.is_owner()
    @commands.command(name="shell", aliases=["sh"], usage="shell <command>")
    async def shell(self, ctx, *, command=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        
        if not command:
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"> {d['args-required']}")
       
        stdout, stderr = await utils.run_process(ctx, command)
        
        if stderr:
            text = f"```\nstdout: \n{stdout} \n\nstderr: \n{stderr}\n```"
        else:
            text = f"```\nstdout: \n{stdout} \n\nstderr: \nnone\n```"
        
        try:
            await ctx.message.add_reaction(self.success)
            return await utils.reply_or_send(ctx, content=text)   
        except Exception as exc:
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"```py\n{exc}\n```")
    
    #system
    @commands.group(name="system", usage="system [args]", invoke_without_command=True)
    @commands.is_owner()
    async def system(self, ctx):
        pass
    
    #help
    @commands.is_owner()
    @system.command(name="help", usage="help [cmd]")
    async def help(self, ctx, cmd=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        
        m = await utils.reply_or_send(ctx, content=f"> {d['loading']}")
        
        if cmd:
            c = self.bot.get_command("system").get_command(cmd)
            if c:
                return await m.edit(content=None, embed=self.generate_help(ctx, d, command=c))
            return await m.edit(content=None, embed=self.generate_help(ctx, d))
        else:
            return await m.edit(content=None, embed=self.generate_help(ctx, d))

    #load
    @commands.is_owner()
    @system.command(name="load", usage="load <file>")
    async def load(self, ctx, *, module=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        
        if not module:
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"> {d['args-required']}")

        try:
            self.bot.load_extension(module)
        except Exception as exc:
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"> {d['error']} \n```py\n{exc.__class__.__name__}: {exc}\n```")
        else:
            await ctx.message.add_reaction(self.success)
    
    #unload
    @commands.is_owner()
    @system.command(name="unload", usage="unload <file>")
    async def unload(self, ctx, *, module=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        
        if not module:
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"> {d['args-required']}")
            
        try:
            self.bot.unload_extension(module)
        except Exception as exc:
            await ctx.message.remove_reaction(self.loading, self.bot.user)
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"> {d['error']} \n```py\n{exc.__class__.__name__}: {exc}\n```")
        else:
            await ctx.message.add_reaction(self.success)
    
    #reload
    @commands.is_owner()
    @system.command(name="reload", aliases=["rl"], usage="reload <file>")
    async def reload(self, ctx, *, module=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        
        if not module:
            cogs = self.bot._ext
            excs = ""
            
            for cog in cogs:
                try:
                    self.bot.reload_extension(cog)
                except Exception as exc:
                    excs += f"{cog} → {exc}\n"

            await ctx.message.add_reaction(self.success)
            
            if excs != "":
                await utils.reply_or_send(ctx, content=f"> {d['failed-loads']} \n```\n{excs}\n```")
            return
        else:
            try:
                self.bot.reload_extension(module)
            except Exception as exc:
                await ctx.message.add_reaction(self.failed)
                return await utils.reply_or_send(ctx, content=f"> {d['error']} \n```py\n{exc.__class__.__name__}: {exc}\n```")
            else:
                await ctx.message.add_reaction(self.success)
    
    #restart
    @commands.is_owner()
    @system.command(name="restart", aliases=["reboot"], usage="restart")
    async def restart(self, ctx):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        
        msg = await utils.reply_or_send(ctx, content=f"> {d['bot-restart']}")
        await self.bot.change_presence(activity=discord.Game(name=f'disabling... Please Wait...'))
        await asyncio.sleep(3)
        
        try:
            await self.bot.close()
        except Exception as exc:
            return await msg.edit(content=f"> {d['error']} \n```py\n{exc}\n```")
        else:
            os.execl(sys.executable, sys.executable, *sys.argv)
    
    #toggle
    @commands.is_owner()
    @system.command(name="toggle", usage="toggle <command>")
    async def toggle(self, ctx, command=None):
        lang = await self.bot.langutil.get_user_lang(ctx.author.id)
        d = await self.bot.langutil.get_lang(lang)
        
        if not command:
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"> {d['args-required']}")
        
        cmd = self.bot.get_command(command)
        if not cmd:
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"> {d['cmd-notfound']}")
        
        if cmd.enabled:
            cmd.enabled = False
        else:
            cmd.enabled = True
        await ctx.message.add_reaction(self.success)

def setup(bot):
    bot.add_cog(mido_admins(bot))
