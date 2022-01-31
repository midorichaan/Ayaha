import asyncio
import subprocess
from discord.ext import commands

#Error while check failed
class NotStaff(commands.errors.CheckFailure):
    pass

#get_public_flags
def get_public_flags(ctx, user):
    flags = dict(user.public_flags)
    result = []

    func = lambda key, value: value and ctx.bot.vars["publicflags"].get(str(key))
    for k, v in flags.items():
        if func(k, v):
            result.append(ctx.bot.vars["publicflags"].get(str(k)))
    return " ".join(i for i in result)

#get_status
def get_status(member, *, db=None):
    status = str(member.status)
    if status == "online":
        return f"💚{db['status-online']}"
    elif status == "idle":
        return f"🧡{db['status-idle']}"
    elif status == "dnd":
        return f"❤{db['status-dnd']}"
    elif status == "offline":
        return f"🖤{db['status-offline']}"
    else:
        return f"💔{db['status-unknown']}"

#reply_or_send
async def reply_or_send(ctx, *args, **kwargs):
    try:
        return await ctx.reply(*args, **kwargs)
    except:
        try:
            return await ctx.send(*args, **kwargs)
        except:
            try:
                return await ctx.author.send(*args, **kwargs)
            except:
                pass

#remove ```
def cleanup_code(content):
    if content.startswith('```') and content.endswith('```'):
        return '\n'.join(content.split('\n')[1:-1])

    return content.strip('` \n')

#create shell process
async def run_process(ctx, command):
    try:
        process = await asyncio.create_subprocess_shell(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = await process.communicate()
    except NotImplementedError:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = await ctx.bot.loop.run_in_executor(None, process.communicate)

    return [output.decode() for output in result]

#check_guild_profile
async def check_guild_profile(bot, guild_id: int):
    db = await bot.db.fetchone("SELECT * FROM guilds WHERE guild_id=%s", (guild_id,))
    if not db:
        await bot.db.register_guild(guild_id)

#is_staff
def is_staff():
    async def predicate(ctx):
        if ctx.author.id in ctx.bot.owner_ids:
            return True

        try:
            db = await ctx.bot.db.fetchone("SELECT * FROM users WHERE user_id=%s", (ctx.author.id,))
        except:
            return False
        else:
            if not db:
                raise NotStaff("Staff rank was required")
            else:
                if db["rank"] >= 2:
                    return True
                raise NotStaff("Staff rank was required")
    return commands.check(predicate)
    
#FetchUserConverter
class FetchUserConverter(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            return await commands.MemberConverter().convert(ctx, argument)
        except:
            try:
                return await commands.UserConverter().convert(ctx, argument)
            except:
                if argument.isdigit():
                    try:
                        return await ctx.bot.fetch_user(int(argument))
                    except:
                        return None
                else:
                    return None

#TextChannelConverter
class TextChannelConverter(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            return await commands.TextChannelConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                channel_id = int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(f"TextChannel {argument!r} not found.")
            else:
                channel = ctx.bot.get_channel(channel_id)
                if channel is None:
                    raise commands.BadArgument(f"TextChannel {argument!r} not found.")
                return channel

#GuildConverter
class GuildConverter(commands.Converter):
    async def convert(self, ctx, argument):
        guild = None
        if argument.isdigit():
            guild = ctx.bot.get_guild(int(argument))

            if guild is None:
                raise commands.BadArgument(f"Guild {argument} not found.")
        else:
            if guild is None:
                guild = discord.utils.get(ctx.bot.guilds, name=argument)
                
                if guild is None:
                    raise commands.BadArgument(f"Guild {argument} not found.")

        return guild
