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

    @commands.command()
    async def karma(self, ctx, user: discord.Member=None):
        if user is None:
            user = ctx.message.author

        cur_karma = self.karma_storage.get(user.id, 0)

        em = discord.Embed()
        em.color = discord.Color.blurple()
        em.set_author(name=str(user), icon_url=user.avatar_url_as(format='png'))
        em.add_field(name='Karma', value=str(cur_karma))

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Karma(bot))
