import asyncio

from discord.ext import commands
from fuzzywuzzy import process
import discord


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.yes_emoji = '\N{WHITE HEAVY CHECK MARK}'
        self.no_emoji = '\N{CROSS MARK}'

    @commands.Cog.listener()
    async def on_member_join(self, member):
        bot_cmds_channel = discord.utils.get(member.guild.text_channels, name="botcommands")
        server_rules_channel = discord.utils.get(member.guild.text_channels, name="server-rules")
        homework_help_channel = discord.utils.get(member.guild.text_channels, name="homeworkhelp")
        try:
            await member.send(f"Welcome, {member.name}!\n\nDon't forget to read the {server_rules_channel.mention} "
                              f" and assign yourself a major in order to access {homework_help_channel.mention}"
                              f" (preferably in the {bot_cmds_channel.mention} channel)!\n\nTo assign yourself a "
                              f"major, type `c major <majorname>`.")
        except:
            pass

    @commands.group(invoke_without_command=True, aliases=["role"])
    @commands.guild_only()
    async def major(self, ctx, *, major: str=''):
        """Gives the user a role based on their area of interest."""

        em = discord.Embed()
        em.color = 0x6e42f4

        roles = await ctx.con.fetch("""
            SELECT role_id, role_name FROM roles ORDER BY role_name ASC;
        """)
        role_names = [r['role_name'] for r in roles]

        if not major:
            em.title = 'Valid Majors'
            em.description = '\n'.join(role_names)
            return await ctx.send(embed=em)

        matches = process.extract(major, role_names, limit=3)
        match = list(max(matches, key=lambda x: x[1]))

        match_name, match_perc = match

        if match_perc != 100:
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

        index = role_names.index(match_name)
        role_id = roles[index]["role_id"]
        role = ctx.guild.get_role(role_id)
        if not role:
            return await ctx.send("Error: role does not exist, contact server administrators")

        if role.id in [r.id for r in ctx.author.roles]:
            await ctx.author.remove_roles(role)
        else:
            await ctx.author.add_roles(role)

        await ctx.message.add_reaction(self.yes_emoji)

    @major.command()
    @commands.has_permissions(administrator=True)
    async def add(self, ctx, *, major: str):
        """Adds a major to the list of valid majors."""
        roles = await ctx.con.fetch("""
            SELECT role_name FROM roles;
        """)
        role_names = [record["role_name"] for record in roles]
        if major in role_names:
            return await ctx.send(f"{major} already exists in the list of valid roles.")

        new_role = await ctx.guild.create_role(name=major, hoist=True)
        await ctx.con.execute("""
            INSERT INTO roles (role_id, role_name) VALUES ($1, $2);
        """, new_role.id, major)

        await ctx.send(f'**{major}** added to list of valid roles.')


    @major.command()
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx, *, major: str):
        """Removes a major from the list of valid majors.

        The name must be exact. Case-sensitive.
        """
        role_id = await ctx.con.fetchval("""
            DELETE FROM roles WHERE role_name=$1 RETURNING role_id;
        """, major)

        role = ctx.guild.get_role(role_id)
        if role:
            await role.delete()
            await ctx.send(f"**{major}** successfully deleted from list of valid roles.")
        else:
            await ctx.send(f"**{major}** not found in list of valid roles. Ensure spelling and capitalization is exact.")

    @major.command()
    async def clear(self, ctx):
        """Attempts to clear all of your flairs."""
        role_ids = await ctx.con.fetch("""
            SELECT role_id FROM roles;
        """)
        role_ids = [record["role_id"] for record in role_ids]

        to_remove = [r for r in ctx.author.roles if r.id in role_ids]
        if not to_remove:
            return

        await ctx.author.remove_roles(*to_remove)
        await ctx.message.add_reaction(self.yes_emoji)


def setup(bot):
    bot.add_cog(General(bot))
