import json

class LangUtil:
    
    def __init__(self, bot):
        self.bot = bot
    
    #get_lang
    async def get_lang(self, author_id: int, *, key: str):
        db = await self.bot.db.fetchone("SELECT * FROM users WHERE user_id=%s", (author_id,))
        lang = "ja-jp"
        keys = None
        
        if not db:
            await self.bot.db.register_user(author_id, lang="ja-jp")
        else:
            lang = db["lang"]
        
        with open(f"./lang/{lang}.json", encoding="utf-8") as f:
            js = json.load(f)
        
            keys = js.get(key, None)
        
        return keys
    
    #get_user_lang
    async def get_user_lang(self, user_id: int):
        db = await self.bot.db.fetchone("SELECT * FROM users WHERE user_id=%s", (user_id,))
        
        if not db:
            return "ja-jp"
        return db["lang"]
