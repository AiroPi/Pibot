import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()


class PiBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()

        super().__init__(
            command_prefix='pi.',
            case_insensitive=True,
            fetch_offline_members=False,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=False),
            intents=intents
        )

        self.load_extension('cogs.pi')
        self.load_extension('cogs.pi_music')

        with open('cogs/ressources/pi.txt', 'r') as f:
            self.pi = f.read()

    async def on_ready(self):
        print("Logged in as : ", self.user.name)
        print("ID : ", self.user.id)

    def run(self, token, test_version=False):
        super().run(token, reconnect=True)


PiBot().run(os.getenv('PI_TOKEN'))
