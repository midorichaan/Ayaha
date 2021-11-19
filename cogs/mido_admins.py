import discord
from discord.ext import commands

import asyncio
import io
import os
import textwrap
import traceback
from contextlib import redirect_stdout
from lib import utils

class mido_admins(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self._ = None
        self.success = "✅"
        self.failed = "❌"
    
    #eval
    @commands.is_owner()
    @commands.command(name="eval", usage="eval <code>")
    async def _eval(self, ctx, *, code: str=None):
        if not code:
            return await utils.reply_or_send(ctx, content=f"> {await self.bot.langutil.get_lang(ctx.author.id, key='args-required')}")
        
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
        if not sql:
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"> {self.bot.langutil.get_lang(ctx.author.id, key='args-required')}")
       
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
        if not command:
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"> {await self.bot.langutil.get_lang(ctx.author.id, key='args-required')}")
       
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
        e = discord.Embed(title="System - system", color=self.bot.color, timestamp=ctx.message.created_at)
        
        if cmd:
            c = self.bot.get_command("system").get_command(cmd)
            
            if c:
                e.title = f"System - {c.name}"
                e.add_field(name=await self.bot.langutil.get_lang(ctx.author.id, key='usage'), value=c.usage)
                e.add_field(name=await self.bot.langutil.get_lang(ctx.author.id, key='description'), value=await self.bot.langutil.get_lang(ctx.author.id, key=f'help-{c.name}'))
                e.add_field(name=await self.bot.langutil.get_lang(ctx.author.id, key='aliases'), value=", ".join([f"`{row}`" for row in c.aliases]))
               
                try:
                   return await utils.reply_or_send(ctx, embed=e)
                except Exception as exc:
                    return await utils.reply_or_send(ctx, content=f"> {await self.bot.langutil.get_lang(ctx.author.id, key='error')} \n```py\n{exc}\n```")
            else:
                for i in self.bot.get_command("system").commands:
                    e.add_field(name=i.usage, value=await self.bot.langutil.get_lang(ctx.author.id, key=f'help-{i.name}'))
            
                try:
                    return await utils.reply_or_send(ctx, embed=e)
                except Exception as exc:
                    return await utils.reply_or_send(ctx, content=f"> {await self.bot.langutil.get_lang(ctx.author.id, key='error')} \n```py\n{exc}\n```")
        else:
            for i in self.bot.get_command("system").commands:
                e.add_field(name=i.usage, value=await self.bot.langutil.get_lang(ctx.author.id, key=f'help-{i.name}'))
            
            try:
                return await utils.reply_or_send(ctx, embed=e)
            except Exception as exc:
                return await utils.reply_or_send(ctx, content=f"> {await self.bot.langutil.get_lang(ctx.author.id, key='error')} \n```py\n{exc}\n```")

    #load
    @commands.is_owner()
    @system.command(name="load", usage="load <file>")
    async def load(self, ctx, *, module=None):
        if not module:
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"> {await self.bot.langutil.get_lang(ctx.author.id, key='args-required')}")

        try:
            self.bot.load_extension(module)
        except Exception as exc:
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"> {await self.bot.langutil.get_lang(ctx.author.id, key='error')} \n```py\n{exc.__class__.__name__}: {exc}\n```")
        else:
            await ctx.message.add_reaction(self.success)
    
    #unload
    @commands.is_owner()
    @system.command(name="unload", usage="unload <file>")
    async def unload(self, ctx, *, module=None):
        if not module:
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"> {await self.bot.langutil.get_lang(ctx.author.id, key='args-required')}")
            
        try:
            self.bot.unload_extension(module)
        except Exception as exc:
            await ctx.message.remove_reaction(self.loading, self.bot.user)
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"> {await self.bot.langutil.get_lang(ctx.author.id, key='error')} \n```py\n{exc.__class__.__name__}: {exc}\n```")
        else:
            await ctx.message.add_reaction(self.success)
    
    #reload
    @commands.is_owner()
    @system.command(name="reload", aliases=["rl"], usage="reload <file>")
    async def reload(self, ctx, *, module=None):
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
                await utils.reply_or_send(ctx, content=f"> {await self.bot.langutil.get_lang(ctx.author.id, key='failed-loads')} \n```\n{excs}\n```")
            return
        else:
            try:
                self.bot.reload_extension(module)
            except Exception as exc:
                await ctx.message.add_reaction(self.failed)
                return await utils.reply_or_send(ctx, content=f"> {await self.bot.langutil.get_lang(ctx.author.id, key='error')} \n```py\n{exc.__class__.__name__}: {exc}\n```")
            else:
                await ctx.message.add_reaction(self.success)
    
    #restart
    @commands.is_owner()
    @system.command(name="restart", aliases=["reboot"], usage="restart")
    async def restart(self, ctx):
        msg = await utils.reply_or_send(ctx, content=f"> {await self.bot.langutil.get_lang(ctx.author.id, key='bot-restart')}")
        await self.bot.change_presence(activity=discord.Game(name=f'disabling... Please Wait...'))
        await asyncio.sleep(3)
        
        try:
            await self.bot.close()
        except Exception as exc:
            await msg.edit(content=f"> {await self.bot.langutil.get_lang(ctx.author.id, key='error')} \n```py\n{exc}\n```")
    
    #toggle
    @commands.is_owner()
    @system.command(name="toggle", usage="toggle <command>")
    async def toggle(self, ctx, command=None):
        if not command:
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"> {await self.bot.langutil.get_lang(ctx.author.id, key='args-required')}")
        
        cmd = self.bot.get_command(command)
        if not cmd:
            await ctx.message.add_reaction(self.failed)
            return await utils.reply_or_send(ctx, content=f"> {await self.bot.langutil.get_lang(ctx.author.id, key='args-required')}")
        
        if cmd.enabled:
            cmd.enabled = False
        else:
            cmd.enabled = True
        await ctx.message.add_reaction(self.success)

def setup(bot):
    bot.add_cog(mido_admins(bot))
