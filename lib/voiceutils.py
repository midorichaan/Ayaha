import re
from . import utils

#_generate
async def _generate(ctx):
    filename = "voicereads/" + ctx.bot.vars["voice"]["filename"]
    message = re.sub(ctx.bot.vars["pattern"]["emoji"], "", ctx.message.content)
    content = str(ctx.author.name) + " " + message
    
    with open(filename, "w", encoding="shift_jis") as f:
        f.write(content)
    
    voice = ctx.bot.vars["voice"]["openjtalk"]
    cmd = [
        voice["path"], 
        "-x", voice["dictionary"]
        "-r", voice["speed"], 
        "-m", voice["htsvoice"],
        "-ow", f'./voicereads/{voice["output"]} ./voicereads/{filename}'
    ]
    
    await utils.run_process(ctx, *cmd)

#create_source
async def create_source(ctx):
    await _generate(ctx)
    return {"id": f"voicereads/{ctx.bot.vars['voice']['filename']}"}
