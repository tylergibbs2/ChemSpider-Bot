import re
import cirpy
import asyncio
import discord

from discord.ext import commands


class Chemistry:
    def __init__(self, bot):
        self.bot = bot
        self.cs = bot.cs

        one = '\N{DIGIT ONE}\N{COMBINING ENCLOSING KEYCAP}'
        two = '\N{DIGIT TWO}\N{COMBINING ENCLOSING KEYCAP}'
        three = '\N{DIGIT THREE}\N{COMBINING ENCLOSING KEYCAP}'
        four = '\N{DIGIT FOUR}\N{COMBINING ENCLOSING KEYCAP}'
        five = '\N{DIGIT FIVE}\N{COMBINING ENCLOSING KEYCAP}'
        self.cancel = '\N{REGIONAL INDICATOR SYMBOL LETTER X}'
        self.next_page = '\N{BLACK RIGHT-POINTING TRIANGLE}'
        self.last_page = '\N{BLACK LEFT-POINTING TRIANGLE}'
        self.num_list = [one, two, three, four, five, self.last_page, self.next_page, self.cancel]

    @commands.command()
    async def search(self, ctx, *, query : str):
        """Searches the ChemSpider database for substances.

        Please note that CAS numbers may be provided in a list
        format due to the inability to check accuracy.
        """

        results = self.cs.search(query)

        await self.bot.loop.run_in_executor(None, results.wait)

        if not results:
            return await ctx.send(f'{query} not found.')

        def user_check(msg):
            return msg.author == ctx.author

        if len(results) != 1:
            result = await self.match_result(results, ctx)
            if not result:
                return await ctx.send(f'Matching failed for {query}, likely timed out or cancelled.')
        else:
            result = results[0]

        cas = await self.bot.loop.run_in_executor(None, cirpy.resolve, result.smiles, 'cas')

        await ctx.send(embed=self.form_embed(result, cas=cas))

    def format_formula(self, formula):
        """Takes a molecular formula and makes the numbers subscripts."""

        def numrepl(match):
            num = match.group(1)
            subscripts = [chr(0x2080 + int(i)) for i in str(num)]
            return ''.join(subscripts)

        sub = re.sub(r'\_\{*([0-9]+)\}', numrepl, formula)

        return sub

    def form_embed(self, compound, **kwargs):
        em = discord.Embed()
        em.color = 0xffa73d

        cas = kwargs.get('cas')

        base_url = r'http://www.chemspider.com/'

        em.title = compound.common_name
        em.url = f'{base_url}Chemical-Structure.{compound.csid}.html'
        em.description = self.format_formula(compound.molecular_formula)

        em.add_field(name='Molecular Weight', value=f'{compound.molecular_weight}g')

        if cas:
            em.add_field(name='Possible CAS Number(s)', value=', '.join(cas[:5]))

        em.set_image(url=compound.image_url)

        return em

    async def match_result(self, results, ctx):

        matching = True

        em = discord.Embed()
        em.color = 0xffa73d

        em.title = 'Multiple results found. Click the reaction for your result.'
        em.description = 'Creating match form...'

        result_pages = [results[i:i+5] for i in range(0, len(results), 5)]
        page_count = len(result_pages)
        page = 0

        list_msg = await ctx.send(embed=em)

        for reaction in self.num_list[:len(result_pages[0])]:
            await list_msg.add_reaction(reaction)
        if page_count > 1:
            await list_msg.add_reaction(self.last_page)
            await list_msg.add_reaction(self.next_page)
        await list_msg.add_reaction(self.cancel)

        while matching:

            em.description = ''

            for i, result in enumerate(result_pages[page]):
                em.description += f'{self.num_list[i]} {result.common_name}\n'
            em.description += f'\n{self.num_list[7]} Cancel'
            if page_count > 1:
                em.description += f'\n{self.num_list[6]} Next Page'
                em.description += f'\n{self.num_list[5]} Previous Page'

            em.set_footer(text=f'Page: {page+1}/{page_count}')

            try:
                await list_msg.edit(content=' ', embed=em)
            except:
                matching = False

            def user_check(rxn, usr):
                return usr.id == ctx.author.id and rxn.message.id == list_msg.id and str(rxn) in self.num_list

            try:
                reaction, member = await self.bot.wait_for('reaction_add', check=user_check, timeout=60)
            except asyncio.TimeoutError:
                await list_msg.delete()
                matching = False

            index = self.num_list.index(str(reaction))
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

def setup(bot):
    bot.add_cog(Chemistry(bot))
