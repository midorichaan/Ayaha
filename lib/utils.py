import asyncio
import subprocess

#reply_or_send
async def reply_or_send(ctx, *args, **kwargs):
    try:
        await ctx.reply(*args, **kwargs)
    except:
        try:
            await ctx.send(*args, **kwargs)
        except:
            try:
                await ctx.author.send(*args, **kwargs)
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

#is_staff
async def is_staff(ctx):
    if ctx.author.id in ctx.bot.owner_ids:
        return True
    
    db = await ctx.bot.db.fetchone("SELECT * FROM users WHERE user_id=%s", (ctx.author.id,))
    if not db:
        return False
    
    return db["rank"] >= 2
    
