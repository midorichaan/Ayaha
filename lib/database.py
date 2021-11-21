from functools import wraps
from typing import Coroutine

import aiomysql

class Database:
    def __init__(
        self, *, host: str = None, port: int = None,
            user: str = None, password: str = None, db: str = None) -> None:
        self.host: str = host
        self.port: int = port
        self.user: str = user
        self.password: str = password
        self.db: str = db
        self.pool: aiomysql.Pool = None

    async def setup(self) -> aiomysql.Pool:
        self.pool = await aiomysql.create_pool(
            host=self.host, port=self.port,
            user=self.user, password=self.password, db=self.db,
            autocommit=True, cursorclass=aiomysql.cursors.DictCursor
        )
        return self.pool

    def check_connection(func) -> Coroutine:
        @wraps(func)
        async def inner(self, *args, **kwargs):
            self.pool = self.pool or await self.setup()
            return await func(self, *args, **kwargs)
        return inner
    
    @check_connection
    async def close(self) -> None:
        self.pool.close()
        await self.pool.wait_closed()

    @check_connection
    async def execute(self, sql: str, *args, **kwargs) -> None:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, *args, **kwargs)

    @check_connection
    async def fetchall(self, sql: str = None, *args, **kwargs) -> None:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                if sql is not None:
                    await cur.execute(sql, *args, **kwargs)
                return await cur.fetchall()
    
    @check_connection
    async def executemany(self, sql: str = None, *args, **kwargs) -> None:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.executemany(sql, *args, **kwargs)

    @check_connection
    async def fetchone(self, sql: str = None, *args, **kwargs) -> None:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                if sql is not None:
                    await cur.execute(sql, *args, **kwargs)
                return await cur.fetchone()
    
    #register_user
    async def register_user(self, author_id: int, *, key: str):
        await self.execute("INSERT INTO users VALUES(%s, %s, %s, %s)", (author_id, key, 0, 0))
    
    #register_guild
    async def register_guild(self, guild_id: int):
        await self.execute("INSERT INTO guilds VALUES(%s, %s, %s, %s, %s)", (guild_id, None, 0, 0, 0))
