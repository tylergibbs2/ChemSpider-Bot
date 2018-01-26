import asyncio

from discord.ext import commands
from fuzzywuzzy import process
import discord


class General:
    def __init__(self, bot):
        self.bot = bot

        self.yes_emoji = '\N{WHITE HEAVY CHECK MARK}'
        self.no_emoji = '\N{CROSS MARK}'

        self.application_questions = [
            'What experience do you have with Discord?',
            'What experience do you have with Chemistry?',
            'Why do you want to be a moderator?'
        ]

    async def on_member_join(self, member):
        bot_cmds_channel = discord.utils.get(member.guild.text_channels, name="botcommands")
        server_rules_channel = discord.utils.get(member.guild.text_channels, name="server-rules")
        homework_help_channel = discord.utils.get(member.guild.text_channels, name="homeworkhelp")
        role_display = '\n'.join(sorted(self.get_chem_roles()))
        try:
            await member.send(f"Welcome, {member.name}!\n\nDon't forget to read the {server_rules_channel.mention} "
                              f" and assign yourself a major in order to access {homework_help_channel.mention}"
                              f" (preferably in the {bot_cmds_channel.mention} channel)!\n\nTo assign yourself a "
                              f"major, type `c major <majorname>` using one of the valid majors below."
                              f"\n\n**Valid Majors**{role_display}")
        except:
            pass

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def major(self, ctx, *, major: str=''):
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
                         f'Is this correct?'

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
    async def add(self, ctx, *, major: str):
        """Adds a major to the list of valid majors."""
        with open('chemMajors.txt', 'a') as f:
            f.write(f'\n{major}')

        await ctx.send(f'{major} added to list of valid majors.')

    @major.command()
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx, *, major: str):
        """Adds a major to the list of valid majors."""
        with open('chemMajors.txt', 'r') as f:
            lines = f.read().splitlines()
        with open('chemMajors.txt', 'w') as f:
            for line in lines:
                if line.lower() != major.lower():
                    f.write(f'{line}\n')

        role = discord.utils.get(ctx.guild.roles, name=major)
        try:
            await role.delete()
        except:
            pass

        await ctx.send(f'Attempted to remove {major} from list of valid majors.')

    @major.command()
    async def clear(self, ctx):
        """Attempts to clear all of your flairs."""
        chem_roles = self.get_chem_roles()

        to_remove = [r for r in ctx.author.roles if r.name in chem_roles]
        if not to_remove:
            return

        await ctx.author.remove_roles(*to_remove)

    def get_chem_roles(self):
        """Returns a list of chemistry majors from a file."""
        with open('chemMajors.txt') as f:
            return f.read().splitlines()

    @commands.command()
    async def modapp(self, ctx):
        """Starts the application process."""
        mod_app_channel = discord.utils.get(ctx.guild.text_channels, id=342325108750155777)
        if not mod_app_channel:
            return

        author = ctx.author

        em = discord.Embed()
        em.color = 0x4286f4
        a_url = author.avatar_url_as(format='png', size=1024)
        em.set_author(name=str(author), icon_url=a_url)
        em.description = ''

        await author.send('Please answer the following questions honestly.')

        def author_check(msg):
            return msg.author.id == author.id

        for question in self.application_questions:
            await author.send(question)
            try:
                resp = await self.bot.wait_for('message', check=author_check, timeout=300)
            except asyncio.TimeoutError:
                return
            em.description += f'{question}:\n{resp.content}\n\n'

        await author.send('Thank you for submitting an application.')

        await mod_app_channel.send(embed=em)


def setup(bot):
    bot.add_cog(General(bot))
