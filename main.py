import discord
import asyncio

from utils import config
from chemspipy import ChemSpider
from discord.ext import commands

description = 'A simple chemistry bot for searching the ChemSpider api.'
creds = config.Config('credentials.json')

base_url = r'http://www.chemspider.com/'

bot = commands.Bot(command_prefix=['c ', 'C '], description=description)
cs = ChemSpider(creds['chemspider'])

one = '\N{DIGIT ONE}\N{COMBINING ENCLOSING KEYCAP}'
two = '\N{DIGIT TWO}\N{COMBINING ENCLOSING KEYCAP}'
three = '\N{DIGIT THREE}\N{COMBINING ENCLOSING KEYCAP}'
four = '\N{DIGIT FOUR}\N{COMBINING ENCLOSING KEYCAP}'
five = '\N{DIGIT FIVE}\N{COMBINING ENCLOSING KEYCAP}'
cancel = '\N{REGIONAL INDICATOR SYMBOL LETTER X}'
num_list = [one, two, three, four, five, cancel]

def form_embed(compound):
    em = discord.Embed()
    em.color = 0xffa73d

    em.title = compound.common_name
    em.url = f'{base_url}Chemical-Structure.{compound.csid}.html'
    em.description = compound.molecular_formula

    em.add_field(name='Molecular Weight', value=str(compound.molecular_weight) + 'g')

    em.set_image(url=compound.image_url)

    return em

async def match_result(results, ctx):
    em = discord.Embed()
    em.color = 0xffa73d

    em.title = 'Multiple results found. Click the reaction for your result.'
    em.description = ''

    length = 5 if len(results) >= 5 else len(results)

    for i, result in enumerate(results[:length]):
        em.description += f'{num_list[i]}. {result.common_name}\n'
    em.description += f'\n{num_list[5]}. Cancel'

    list_msg = await ctx.send(embed=em)

    for emoji in num_list[:length]:
        await list_msg.add_reaction(emoji)

    rxn_list = [str(reaction) for reaction in list_msg.reactions]
    if cancel not in rxn_list:
        await list_msg.add_reaction(cancel)

    def user_check(rxn, usr):
        return usr.id == ctx.author.id and rxn.message.id == list_msg.id

    try:
        reaction, member = await bot.wait_for('reaction_add', check=user_check)
    except asyncio.TimeoutError:
        await list_msg.delete()
        return

    await list_msg.delete()

    if str(reaction) not in num_list:
        return

    index = num_list.index(str(reaction))

    if index == 5:
        return

    return results[index]


@bot.event
async def on_ready():
    await bot.change_presence(game=discord.Game(name='c search'))
    print('ready')

@bot.command()
async def search(ctx, *, search : str):
    """Searches the ChemSpider database for substances."""

    results = cs.search(search)

    await bot.loop.run_in_executor(None, results.wait)

    if not results:
        return await ctx.send('Compound not found.')

    def user_check(msg):
        return msg.author == ctx.author

    if len(results) != 1:
        result = await match_result(results, ctx)
        if not result:
            return await ctx.send('Matching failed, likely timed out or cancelled.')
    else:
        result = results[0]

    await ctx.send(embed=form_embed(result))

@bot.command(hidden=True)
@commands.is_owner()
async def logout(ctx):
    await bot.logout()

bot.run(creds['token'])
