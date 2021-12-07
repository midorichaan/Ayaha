import discord

class DatabaseNotFound(Exception):
    pass

class NotTicket(Exception):
    pass

class TicketUtil:
    
    def __init__(self, bot):
        self.bot = bot
    
    """
    Ticket機能各DB情報
    
    ・tickets - チケットチャンネルの情報
       ticket_id : チケットチャンネルのID
       guild_id : サーバーID
       author_id : 作成者のID
       created_at : チケットの作成日時
       status : チケットのステータス (0 = クローズ, 1 = オープン, 2 = 理由待ち)
       reason : チケットの作成理由
    
    ・ticketpanels - チケット作成パネルの情報
       panel_id : パネルのID
       guild_id : サーバーID
       channel_id : チャンネルID
       author_id : 作成者のID
       created_at : パネルの作成日時
    """
    
    #create_ticket
    async def create_ticket(self, guild_id: int, author_id: int, ticket_id: int, *, reason: str=None):
        if not reason:
            status = 2
        else:
            status = 1
        
        await self.bot.db.execute(
            "INSERT INTO tickets VALUES(%s, %s, %s, %s, %s, %s)",
            (ticket_id, guild_id, author_id, datetime.datetime.now(), status, reason)
        )
    
    #delete_ticket
    async def delete_ticket(self, ticket_id: int):
        data = await self.get_ticket(ticket_id)
        if not data:
            raise DatabaseNotFound(f"ticket_id {ticket_id} was not found")
        
        await self.bot.db.execute("DELETE FROM tickets WHERE ticket_id=%s", (ticket_id,))
    
    #db_init
    async def db_init(self):
        query = [
            "CREATE TABLE IF NOT EXISTS " \
            "tickets(ticket_id BIGINT PRIMARY KEY NOT NULL, guild_id BIGINT, author_id BIGINT, created_at TEXT, status INT, reason TEXT)",
            "CREATE TABLE IF NOT EXISTS " \
            "ticketpanels(panel_id BIGINT PRIMARY KEY NOT NULL, guild_id BIGINT, channel_id BIGINT, author_id BIGINT, created_at TEXT)"
        ]
        
        for i in query:
            await self.bot.db.execute(i)
        
    #register_ticket
    async def register_ticket(self, *, channel_id: int=None, guild_id: int=None, author_id: int=None, created_at: str=None):
        await self.bot.db.execute(
            "INSERT INTO tickets VALUES(%s, %s, %s, %s, %s, %s)", 
            (channel_id, guild_id, author_id, created_at, 2, None)
        )
    
    #register_panel
    async def register_panel(self, *, panel_id: int=None, guild_id: int=None, channel_id: int=None, author_id: int=None, created_at: str=None):
        await self.bot.db.execute(
            "INSERT INTO ticketpanels VALUES(%s, %s, %s, %s, %s)",
            (panel_id, guild_id, channel_id, author_id, created_at)
        )
    
    #create_panel
    async def create_panel(self, *, guild_id: int):
        db = await self.bot.db.fetchone("SELECT * FROM ticketconfig WHERE guild_id=%s", (guild_id,))
        e = discord.Embed(title=discord.Embed.Empty, description=discord.Embed.Empty, color=self.bot.color)
        
        if db["ticket_panel_title"]:
            e.title = db["ticket_panel_title"]
        else:
            e.title = "Ticket Panel"
        if db["ticket_panel_description"]:
            e.description = db["ticket_panel_description"]
        
        return e
    
    #get_tickets
    async def get_tickets(self):
        db = await self.bot.db.fetchall("SELECT * FROM tickets")
        return db
    
    #get_panels
    async def get_panels(self):
        db = await self.bot.db.fetchall("SELECT * FROM ticketpanels")
        return db
    
    #get_ticket
    async def get_ticket(self, ticket_id: int):
        db = await self.bot.db.fetchone("SELECT * FROM tickets WHERE ticket_id=%s", (ticket_id,))
        return db
    
    #edit_reason
    async def edit_reason(self, ticket_id: int, *, reason: str):
        db = await self.bot.db.fetchone("SELECT * FROM tickets WHERE ticket_id=%s", (ticket_id,))
        
        if not db:
            raise NotTicket("ID {} is not ticket id".format(ticket_id))
        
        await self.bot.db.execute("UPDATE tickets SET reason=%s WHERE ticket_id=%s", (reason, ticket_id))
    
    #delete_ticket
    async def delete_ticket(self, ticket_id: int):
        db = await self.get_ticket(ticket_id)
        
        if not db:
            raise DatabaseNotFound("Ticket {} was not found".format(ticket_id))
        
        await self.bot.db.execute("DELETE FROM tickets WHERE ticket_id=%s", (ticket_id,))
    
    #get_panel
    async def get_panel(self, panel_id: int):
        db = await self.bot.db.fetchone("SELECT * FROM ticketpanels WHERE panel_id=%s", (panel_id,))
        return db
    
    #delete_panel
    async def delete_panel(self, panel_id: int):
        db = await self.bot.db.fetchone("SELECT * FROM ticketpanels WHERE panel_id=%s", (panel_id,))
        
        if not db:
            raise DatabaseNotFound("Ticket Panel {} was not found".format(panel_id))
        
        await self.bot.db.execute("DELETE FROM ticketpanels WHERE panel_id=%s", (panel_id,))
    
    #panel_exists
    async def panel_exists(self, *, panel_id: int):
        db = await self.bot.db.fetchone("SELECT * FROM ticketpanels WHERE panel_id=%s", (panel_id,))
        
        if db:
            return db
        return False
