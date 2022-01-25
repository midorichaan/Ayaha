import json

class LangUtil:
    
    def __init__(self, bot):
        self.bot = bot
        
    #get_data
    async def get_data(self, user_id: int):
        db = await self.bot.db.fetchone("SELECT * FROM users WHERE user_id=%s", (user_id,))
        if not db:
            await self.bot.db.register_user(user_id, lang="ja-jp")
            return await self.bot.db.fetchone("SELECT * FROM users WHERE user_id=%s", (user_id,))
        return db
    
    #get_lang
    async def get_lang(self, lang: str):
        with open(f"./lang/{lang}.json", encoding="utf-8") as f:
            js = json.load(f)
            return js
    
    #get_key
    async def get_key(self, lang: str, key: str):
        with open(f"./lang/{lang}.json", encoding="utf-8") as f:
            js = json.load(f)
        
            return js.get(key, None)
    
    #get_user_lang
    async def get_user_lang(self, user_id: int):
        try:
            db = await self.get_data(user_id)
        except:
            return "ja-jp"
        else:
            return db["lang"]

    #set_user_lang
    async def set_user_lang(self, user_id: int, *, lang: str):
        await self.bot.db.execute("UPDATE users SET lang=%s WHERE user_id=%s", (lang, user_id))
