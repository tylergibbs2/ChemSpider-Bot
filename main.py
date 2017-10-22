import traceback

from chemspipy import ChemSpider
from discord.ext import commands
import discord

from utils import config


description = 'A simple chemistry bot for searching the ChemSpider api.'
creds = config.Config('credentials.json')

bot = commands.Bot(command_prefix=['c ', 'C '], description=description)
bot.cs = ChemSpider(creds['chemspider'])

startup_cogs = [
    'cogs.chemistry',
    'cogs.general',
    'cogs.admin'
    ]


@bot.event
async def on_ready():
    await bot.change_presence(game=discord.Game(name='c search'))
    print('ready')


@bot.event
async def on_command_error(ctx, exc):
    e = getattr(exc, 'original', exc)
    if isinstance(e, (commands.MissingRequiredArgument, commands.BadArgument)):
        await ctx.invoke(bot.get_command('help'), ctx.command.name)
    else:
        tb = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        print(tb)

if __name__ == "__main__":
    for extension in startup_cogs:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print('{}: {}'.format(type(e).__name__, e))

bot.run(creds['token'])
