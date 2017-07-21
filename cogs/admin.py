import datetime
import discord
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
    async def load(self, ctx, *, module : str):
        """Loads a cog."""
        try:
            self.bot.load_extension(module)
        except Exception as e:
            await ctx.send(content='{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send(content=f'{module} loaded.')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx, *, module : str):
        """Unloads a cog."""
        try:
            self.bot.unload_extension(module)
        except Exception as e:
            await ctx.send(content='{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send(content=f'{module} unloaded.')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, *, module : str):
        """Reloads a cog."""
        try:
            self.bot.unload_extension(module)
            self.bot.load_extension(module)
        except Exception as e:
            await ctx.send(content='{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send(content=f'{module} reloaded.')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def debug(self, ctx, *, code: str):
        """Evaluates code."""

        code = code.strip('` ')
        python = '```py\n{}\n```'
        result = None

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
