import asyncio
import discord

from discord.ext import commands
from fuzzywuzzy import process

class General:
    def __init__(self, bot):
        self.bot = bot

        self.yes_emoji = '\N{WHITE HEAVY CHECK MARK}'
        self.no_emoji = '\N{CROSS MARK}'

    @commands.group(invoke_without_command=True)
    async def major(self, ctx, *, major : str=''):
        """Gives the user a role based on their area of interest."""

        em = discord.Embed()
        em.color = 0x6e42f4

        chem_roles = self.get_chem_roles()

        if not major:
            em.title = 'Valid Majors'
            em.description = '\n'.join(sorted(chem_roles))
            return await ctx.send(embed=em)

        matches = process.extract(major, chem_roles, limit=3)
        match = list(max(matches, key=lambda x: x[1]))

        match_name = match[0]
        match_perc = match[1]

        em.title = match_name
        em.description = f'{match_perc}% match!\n\n' \
                        'Is this correct?'

        match_msg = await ctx.send(embed=em)

        await match_msg.add_reaction(self.yes_emoji)
        await match_msg.add_reaction(self.no_emoji)

        def reaction_check(reaction, user):
            if str(reaction) == self.yes_emoji or str(reaction) == self.no_emoji:
                return user.id == ctx.author.id
            return False

        try:
            rxn, user = await self.bot.wait_for('reaction_add', check=reaction_check, timeout=60)
        except asyncio.TimeoutError:
            return await match_msg.delete()
        await match_msg.delete()

        if str(rxn) == self.no_emoji:
            return

        role = discord.utils.get(ctx.guild.roles, name=match_name)
        if not role:
            role = await ctx.guild.create_role(name=match_name, hoist=True)

        await ctx.author.add_roles(role)

    @major.command()
    @commands.has_permissions(administrator=True)
    async def add(self, ctx, *, major : str):
        """Adds a major to the list of valid majors."""
        with open('chemMajors.txt', 'a') as f:
            f.write(f'\n{major}')

        await ctx.send(f'{major} added to list of valid majors.')

    @major.command()
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx, *, major : str):
        """Adds a major to the list of valid majors."""
        with open('chemMajors.txt', 'r') as f:
            lines = f.read().splitlines()
        with open('chemMajors.txt', 'w') as f:
            for line in lines:
                if line.lower() != major.lower():
                    f.write(f'{line}\n')

        await ctx.send(f'Attempted to remove {major} from list of valid majors.')

    def get_chem_roles(self):
        """Returns a list of chemistry majors from a file."""
        with open('chemMajors.txt') as f:
            return f.read().splitlines()

def setup(bot):
    bot.add_cog(General(bot))
