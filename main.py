import io
import re
import random
import discord
import asyncio
import inspect

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
next_page = '\N{BLACK RIGHT-POINTING TRIANGLE}'
last_page = '\N{BLACK LEFT-POINTING TRIANGLE}'
num_list = [one, two, three, four, five, last_page, next_page, cancel]

def format_formula(formula):
    """Takes a molecular formula and makes the numbers subscripts."""

    def numrepl(match):
        num = match.group(1)
        subscripts = [chr(0x2080 + int(i)) for i in str(num)]
        return ''.join(subscripts)

    sub = re.sub(r'\_\{*([0-9]+)\}', numrepl, formula)

    return sub

def form_embed(compound):
    em = discord.Embed()
    em.color = 0xffa73d

    em.title = compound.common_name
    em.url = f'{base_url}Chemical-Structure.{compound.csid}.html'
    em.description = format_formula(compound.molecular_formula)

    em.add_field(name='Molecular Weight', value=str(compound.molecular_weight) + 'g')

    em.set_image(url=compound.image_url)

    return em

async def match_result(results, ctx):

    matching = True

    em = discord.Embed()
    em.color = 0xffa73d

    em.title = 'Multiple results found. Click the reaction for your result.'
    em.description = 'Creating match form...'

    result_pages = [results[i:i+5] for i in range(0, len(results), 5)]
    page_count = len(result_pages)
    page = 0

    list_msg = await ctx.send(embed=em)

    for reaction in num_list[:len(result_pages[0])]:
        await list_msg.add_reaction(reaction)
    if page_count > 1:
        await list_msg.add_reaction(last_page)
        await list_msg.add_reaction(next_page)
    await list_msg.add_reaction(cancel)

    while matching:

        em.description = ''

        for i, result in enumerate(result_pages[page]):
            em.description += f'{num_list[i]} {result.common_name}\n'
        em.description += f'\n{num_list[7]} Cancel'
        if page_count > 1:
            em.description += f'\n{num_list[6]} Next Page'
            em.description += f'\n{num_list[5]} Previous Page'

        em.set_footer(text=f'Page: {page+1}/{page_count}')

        try:
            await list_msg.edit(content=' ', embed=em)
        except:
            matching = False

        def user_check(rxn, usr):
            return usr.id == ctx.author.id and rxn.message.id == list_msg.id and str(rxn) in num_list

        try:
            reaction, member = await bot.wait_for('reaction_add', check=user_check, timeout=60)
        except asyncio.TimeoutError:
            await list_msg.delete()
            matching = False

        index = num_list.index(str(reaction))
        if index == 7:
            matching = False
        elif index == 6:
            page += 1
            if page > page_count-1:
                page = page_count-1
        elif index == 5:
            page -= 1
            if page < 0:
                page = 0
        elif 0 <= index <= 4:
            break

        try:
            await list_msg.remove_reaction(reaction.emoji, member)
        except:
            pass

    else:
        await list_msg.delete()
        return

    await list_msg.delete()

    try:
        result = result_pages[page][index]
    except IndexError:
        return

    return result


@bot.event
async def on_ready():
    await bot.change_presence(game=discord.Game(name='c search'))
    print('ready')

@bot.command()
async def search(ctx, *, query : str):
    """Searches the ChemSpider database for substances."""

    results = cs.search(query)

    await bot.loop.run_in_executor(None, results.wait)

    if not results:
        return await ctx.send(f'{query} not found.')

    def user_check(msg):
        return msg.author == ctx.author

    if len(results) != 1:
        result = await match_result(results, ctx)
        if not result:
            return await ctx.send(f'Matching failed for {query}, likely timed out or cancelled.')
    else:
        result = results[0]

    await ctx.send(embed=form_embed(result))

@bot.command()
async def meme(ctx):
    """Sends a random message from the #chemistry-memes channel."""
    if ctx.guild.id != 331174943679315979:
        return

    meme_channel = discord.utils.get(ctx.guild.text_channels, name='chemistry-memes')
    if not meme_channel:
        return

    message = random.choice(await channel.history(limit=1000).flatten())

    if message.attachments:
        em = discord.Embed()
        em.color = 0xffa73d

        attachment = message.attachments[0]
        b = io.BytesIO()
        await attachment.save(b)
        b.seek(0)
        if attachment.height:
            em.set_image(url=f'attachment://{attachment.filename}')

        try:
            await ctx.send(file=discord.File(b, attachment.filename), embed=em)
        except:
            pass
        return

    await ctx.send(message.content)

@bot.command(hidden=True)
@commands.is_owner()
async def logout(ctx):
    await bot.logout()

@bot.command(hidden=True)
@commands.is_owner()
async def debug(ctx, *, code: str):
    """Evaluates code."""

    code = code.strip('` ')
    python = '```py\n{}\n```'
    result = None

    env = {
        'bot': bot,
        'ctx': ctx,
        'message': ctx.message,
        'guild': ctx.guild,
        'channel': ctx.channel,
        'author': ctx.author
    }

    env.update(globals())

    try:
        result = eval(code, env)
        if inspect.isawaitable(result):
            result = await result
    except Exception as e:
        await ctx.send(python.format(type(e).__name__ + ': ' + str(e)))
        return

    await ctx.send(python.format(result))

bot.run(creds['token'])
