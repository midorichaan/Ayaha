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
