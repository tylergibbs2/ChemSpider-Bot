from discord.ext import commands
import discord


class Karma(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, rxn, usr):
        if not isinstance(rxn.emoji, discord.Emoji) or rxn.emoji.name not in ['upvote', 'downvote']:
            return

        if rxn.message.author.id == usr.id:
            return

        async with self.bot.db_pool.acquire() as con:
            await con.execute("""
            INSERT INTO karma (message_id, karma_type, giver, receiver) VALUES ($1, $2, $3, $4);
        """, rxn.message.id, rxn.emoji.name, usr.id, rxn.message.author.id)

    @commands.Cog.listener()
    async def on_reaction_remove(self, rxn, usr):
        if not isinstance(rxn.emoji, discord.Emoji) or rxn.emoji.name not in ['upvote', 'downvote']:
            return

        if rxn.message.author.id == usr.id:
            return

        async with self.bot.db_pool.acquire() as con:
            await con.execute("""
                DELETE FROM karma WHERE message_id=$1 AND karma_type=$2 AND giver=$3 AND receiver=$4;
            """, rxn.message.id, rxn.emoji.name, usr.id, rxn.message.author.id)

    @commands.group(invoke_without_command=True)
    async def karma(self, ctx, user: discord.Member=None):
        """View the karma of yourself or another user."""
        if user is None:
            user = ctx.message.author

        karma = await ctx.con.fetchval("""
            SELECT get_karma($1);
        """, user.id)

        em = discord.Embed()
        em.color = discord.Color.blurple()
        em.set_author(name=str(user), icon_url=user.avatar_url_as(format='png'))
        em.add_field(name='Karma', value=str(karma))

        await ctx.send(embed=em)

    @karma.command(name='top', aliases=['highest'])
    async def k_top(self, ctx):
        """View the users with the top karma in the guild."""
        users = await ctx.con.fetch("""
            SELECT DISTINCT receiver, get_karma(receiver) as karma_ct FROM karma ORDER BY karma_ct DESC LIMIT 5;
        """)
        
        em = discord.Embed()
        em.color = discord.Color.blurple()
        em.title = 'Top Karma Users'
        em.description = ''
        for i, user in enumerate(users):
            user_obj = self.bot.get_user(user["receiver"])
            if user_obj is None:
                user_obj = await self.bot.fetch_user(user["receiver"])

            if user_obj is None:
                user_display = "*Deleted User*"
            else:
                user_display = user_obj.mention

            em.description += f"{i+1}. {user_display} ({user['karma_ct']} karma)\n"

        await ctx.send(embed=em)

    @karma.command(name='bottom', aliases=['lowest'])
    async def k_bottom(self, ctx):
        """View the users with the lowest karma in the guild."""
        users = await ctx.con.fetch("""
            SELECT DISTINCT receiver, get_karma(receiver) as karma_ct FROM karma ORDER BY karma_ct ASC LIMIT 5;
        """)
        
        em = discord.Embed()
        em.color = discord.Color.blurple()
        em.title = 'Top Karma Users'
        em.description = ''
        for i, user in enumerate(users):
            user_obj = self.bot.get_user(user["receiver"])
            if user_obj is None:
                user_obj = await self.bot.fetch_user(user["receiver"])

            if user_obj is None:
                user_display = "*Deleted User*"
            else:
                user_display = user_obj.mention
            em.description += f"{i+1}. {user_display} ({user['karma_ct']} karma)\n"

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Karma(bot))
