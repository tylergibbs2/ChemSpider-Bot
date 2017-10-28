from discord.ext import commands
import discord

from utils import config


class Karma:
    def __init__(self, bot):
        self.bot = bot
        self.karma_storage = config.Config('karma.json')

    async def on_reaction_add(self, rxn, user):
        if rxn.emoji.name not in ['upvote', 'downvote']:
            return

        if rxn.message.author.id == user.id:
            return

        current_karma = self.karma_storage.get(rxn.message.author.id, 0)
        if rxn.emoji.name == 'upvote':
            current_karma += 1
        elif rxn.emoji.name == 'downvote':
            current_karma -= 1

        await self.karma_storage.put(rxn.message.author.id, current_karma)

    async def on_reaction_remove(self, rxn, user):
        if rxn.emoji.name not in ['upvote', 'downvote']:
            return

        if rxn.message.author.id == user.id:
            return

        current_karma = self.karma_storage.get(rxn.message.author.id, 0)
        if rxn.emoji.name == 'upvote':
            current_karma -= 1
        elif rxn.emoji.name == 'downvote':
            current_karma += 1

        await self.karma_storage.put(rxn.message.author.id, current_karma)

    @commands.group(invoke_without_command=True)
    async def karma(self, ctx, user: discord.Member=None):
        """View the karma of yourself or another user."""
        if user is None:
            user = ctx.message.author

        cur_karma = self.karma_storage.get(user.id, 0)

        em = discord.Embed()
        em.color = discord.Color.blurple()
        em.set_author(name=str(user), icon_url=user.avatar_url_as(format='png'))
        em.add_field(name='Karma', value=str(cur_karma))

        await ctx.send(embed=em)

    @karma.command(name='top', aliases=['highest'])
    async def k_top(self, ctx):
        """View the users with the top karma in the guild."""
        all_karma = self.karma_storage.all()
        top_five = sorted(all_karma, key=all_karma.get, reverse=True)[:5]
        top_five_users = [discord.utils.get(ctx.guild.members, id=int(item)) for item in top_five]

        em = discord.Embed()
        em.color = discord.Color.blurple()
        em.title = 'Top Karma Users'
        em.description = '\n'.join([f'{i+1}. {m.mention} ({all_karma[str(m.id)]} karma)' if m is not None else
                                    f'{i+1}. User not in Server'
                                    for (i, m) in enumerate(top_five_users)])

        await ctx.send(embed=em)

    @karma.command(name='bottom', aliases=['lowest'])
    async def k_bottom(self, ctx):
        """View the users with the lowest karma in the guild."""
        all_karma = self.karma_storage.all()
        top_five = sorted(all_karma, key=all_karma.get)[:5]
        top_five_users = [discord.utils.get(ctx.guild.members, id=int(item)) for item in top_five]

        em = discord.Embed()
        em.color = discord.Color.blurple()
        em.title = 'Bottom Karma Users'
        em.description = '\n'.join([f'{i+1}. {m.mention} ({all_karma[str(m.id)]} karma)' if m is not None else
                                    f'{i+1}. User not in Server'
                                    for (i, m) in enumerate(top_five_users)])

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Karma(bot))
