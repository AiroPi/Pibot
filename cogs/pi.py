import asyncio

import discord
from discord.ext import commands

from main import PiBot


class Pi(commands.Cog):
    def __init__(self, bot: PiBot):
        self.bot = bot

    @commands.command(name='pi')
    async def _pi(self, ctx):
        def create_pi_embed():
            embed = discord.Embed(title='Voici π',
                                  description=f"`{'...' * bool(index)}{self.bot.pi[index:index + 1000]}...`")
            return embed

        index = 0
        message = await ctx.send(embed=create_pi_embed())

        await message.add_reaction('◀️')
        await message.add_reaction('▶️')

        def check(react: discord.Reaction, usr: discord.User) -> bool:
            return usr == ctx.message.author and react.message == message and str(react.emoji) in ['◀️', '▶️']

        while True:
            try: reaction, _ = await self.bot.wait_for('reaction_add', timeout=500, check=check)
            except asyncio.TimeoutError: break

            if str(reaction.emoji) == '◀️':
                index -= 1000
                if index < 0: index = 0
            elif str(reaction.emoji) == '▶️':
                index += 1000
                if index > 10_000_000 - 1000: index = 10_000_000 - 1000

            try: await message.edit(embed=create_pi_embed())
            except Exception: break

    @commands.command(name='infos')
    async def _infos(self, ctx):
        embed = discord.Embed(title='Quelques informations sur π',
                              description="J'en ai pas encore.")
        await ctx.send(embed=embed)

    @commands.command(name='date')
    async def _date(self, ctx, *, date):
        day, month, year = date.split('/')  # TODO : use a regex to match different date format

        try: index = self.bot.pi.index(str(day) + str(month) + str(year))
        except:
            return await ctx.send(f"Date not found. I thought that 10,000,000 decimals of π was enough to have all possible dates, but I was wrong.")

        pi = self.bot.pi

        embed = discord.Embed(title=f'Here is your π-date (at π-index {index})',
                              description=f"`{'...' * bool(index)}{pi[index - min(475, index):index]}`**→`{pi[index:index + 6]}`←**`{pi[index:index + min(475, 10_000_000 - index)]}...`")
        await ctx.send(embed=embed)


def setup(bot: PiBot):
    bot.add_cog(Pi(bot))
