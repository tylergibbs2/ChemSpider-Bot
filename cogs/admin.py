import inspect

from discord.ext import commands


class Admin:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def logout(self, ctx):
        """Logs out the bot."""
        await self.bot.logout()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def load(self, ctx, *, ext: str):
        """Loads a cog."""
        try:
            self.bot.load_extension(ext)
        except Exception as e:
            await ctx.send(content='{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send(content=f'{ext} loaded.')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx, *, ext: str):
        """Unloads a cog."""
        try:
            self.bot.unload_extension(ext)
        except Exception as e:
            await ctx.send(content='{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send(content=f'{ext} unloaded.')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, *, ext: str):
        """Reloads a cog."""
        try:
            self.bot.unload_extension(ext)
            self.bot.load_extension(ext)
        except Exception as e:
            await ctx.send(content='{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send(content=f'{ext} reloaded.')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def debug(self, ctx, *, code: str):
        """Evaluates code."""

        code = code.strip('` ')
        python = '```py\n{}\n```'

        env = {
            'bot': self.bot,
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


def setup(bot):
    bot.add_cog(Admin(bot))
