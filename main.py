import datetime
import traceback

import asyncpg
from chemspipy import ChemSpider
from discord.ext import commands
import discord

import config


class ChemSpiderBot(commands.Bot):
    async def on_ready(self):
        if not hasattr(self, "uptime"):
            self.uptime = datetime.datetime.utcnow()

        await bot.change_presence(activity=discord.Game(name='c search'))
        print('ready')


    async def process_commands(self, message):
        ctx = await self.get_context(message)

        if ctx.command is None:
            return

        ctx.con = await self.db_pool.acquire()
        await self.invoke(ctx)
        await self.db_pool.release(ctx.con)


    async def on_command_error(self, ctx, exc):
        e = getattr(exc, 'original', exc)
        if isinstance(e, (commands.MissingRequiredArgument, commands.BadArgument)):
            await ctx.invoke(bot.get_command('help'), ctx.command.name)
        else:
            tb = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            print(tb)


description = 'A simple chemistry bot for searching the ChemSpider API.'

intents = discord.Intents.default()

bot = ChemSpiderBot(command_prefix=['c ', 'C '], description=description, intents=intents)
bot.cs = ChemSpider(config.CHEMSPIDER)
bot.db_pool = bot.loop.run_until_complete(asyncpg.create_pool(config.PSQL_DSN))

startup_cogs = [
    'cogs.chemistry',
    'cogs.general',
    'cogs.karma',
    'jishaku'
]

if __name__ == "__main__":
    for extension in startup_cogs:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print('{}: {}'.format(type(e).__name__, e))

bot.run(config.TOKEN)
