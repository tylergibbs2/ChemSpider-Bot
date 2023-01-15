from __future__ import annotations

import datetime
import traceback
from typing import Optional

import asyncpg
from chemspipy import ChemSpider
from discord.ext import commands
import discord

import config


cogs = (
    'cogs.chemistry',
    'cogs.general',
    'cogs.karma',
    'jishaku'
)

class ChemSpiderBot(commands.Bot):
    cs: ChemSpider
    db_pool: Optional[asyncpg.pool.Pool] = None

    def __init__(self, *args, **kwargs):
        self.cs = ChemSpider(config.CHEMSPIDER)

        intents = discord.Intents.all()
        super().__init__(*args, **kwargs, intents=intents)

    async def setup_hook(self) -> None:
        self.db_pool = await asyncpg.create_pool(config.PSQL_DSN)

        for cog in cogs:
            print(f"Loading cog '{cog}'...")
            await self.load_extension(cog)
            print(f"Loaded cog '{cog}'.")

    async def on_ready(self):
        if not hasattr(self, "uptime"):
            self.uptime = datetime.datetime.utcnow()

        await bot.change_presence(activity=discord.Game(name='c search'))
        print('ready')

    async def process_commands(self, message):
        if self.db_pool is None:
            print("no db pool, skipping command")
            return

        ctx = await self.get_context(message)
        if ctx.command is None:
            return

        ctx.con = await self.db_pool.acquire()  # type: ignore
        await self.invoke(ctx)
        await self.db_pool.release(ctx.con)  # type: ignore

    async def on_command_error(self, ctx, exc: Exception):
        e: Exception = getattr(exc, 'original', exc)
        if isinstance(e, (commands.MissingRequiredArgument, commands.BadArgument)):
            await ctx.invoke(bot.get_command('help'), ctx.command.name)
        else:
            traceback.print_tb(e.__traceback__)


description = 'A simple chemistry bot for searching the ChemSpider API.'
bot = ChemSpiderBot(command_prefix=['c ', 'C '], description=description)

if __name__ == "__main__":
    bot.run(config.TOKEN)
