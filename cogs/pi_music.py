import subprocess
import shlex
import io
import asyncio

from pydub import AudioSegment
import discord
from discord.ext import commands
from discord.opus import Encoder

from main import PiBot


class FFmpegPCMAudio(discord.AudioSource):
    def __init__(self, source, *, executable='ffmpeg', pipe=False, stderr=None, before_options=None, options=None):
        stdin = None if not pipe else source
        args = [executable]
        if isinstance(before_options, str):
            args.extend(shlex.split(before_options))
        args.append('-i')
        args.append('-' if pipe else source)
        args.extend(('-f', 's16le', '-ar', '48000', '-ac', '2', '-loglevel', 'warning'))
        if isinstance(options, str):
            args.extend(shlex.split(options))
        args.append('pipe:1')
        self._process = None
        try:
            self._process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr)
            self._stdout = io.BytesIO(
                self._process.communicate(input=stdin)[0]
            )
        except FileNotFoundError:
            raise discord.ClientException(executable + ' was not found.') from None
        except subprocess.SubprocessError as exc:
            raise discord.ClientException('Popen failed: {0.__class__.__name__}: {0}'.format(exc)) from exc

    def read(self):
        ret = self._stdout.read(Encoder.FRAME_SIZE)
        if len(ret) != Encoder.FRAME_SIZE:
            return b''
        return ret

    def cleanup(self):
        proc = self._process
        if proc is None:
            return
        proc.kill()
        if proc.poll() is None:
            proc.communicate()

        self._process = None


class PiMusic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        notes = ['a3', 'b5', 'c4', 'd4', 'e4', 'f4', 'g4', 'a4', 'b4', 'c5']

        self.pi_note = {}
        for i, note in enumerate(notes):
            self.pi_note[i] = AudioSegment.from_file(f'cogs/ressources/piano2/{note}.m4a', format="m4a")

        self.players = {}

    @commands.command(name='play')
    @commands.bot_has_permissions(send_messages=True)
    async def _play(self, ctx, speed: int = 350, volume: int = 100):
        user_voice = ctx.author.voice
        if not user_voice:  # si l'utilisateur n'est pas connecté à un salon vocal
            return await ctx.send('Please first join a voice channel :)')

        user_voice_channel: discord.VoiceChannel = user_voice.channel

        bot_perms = user_voice_channel.permissions_for(ctx.me)
        missing = [perm for perm in ["speak", "connect"] if not getattr(bot_perms, perm)]
        if missing:
            return await ctx.send(f"😢 It's look like I can't connect to the channel <#{user_voice_channel.id}>")
            #  raise commands.errors.BotMissingPermissions(missing)

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():  # si le bot est connecté a un channel vocal
            await voice.move_to(user_voice_channel)  # bouge dans le salon
        else:
            voice = await user_voice_channel.connect()  # se connecte au channel

        if voice.is_playing():
            self.players.pop(ctx.channel.id)
            voice.stop()

        async def create_music(i):
            principal = AudioSegment.silent(duration=25 * speed)
            for i, decimal in enumerate(self.bot.pi[i:i + 25]):
                principal = principal.overlay(self.pi_note[int(decimal)], position=i * speed)
            buffer = io.BytesIO()
            principal.export(buffer, format='wav')
            self.players[ctx.channel.id] = discord.PCMVolumeTransformer(FFmpegPCMAudio(buffer.read(), pipe=True, before_options='-guess_layout_max 0'), volume/400)

        index = 0
        await create_music(0)

        def play_note(error):
            nonlocal index
            index += 25

            if not error:
                if self.players.get(ctx.channel.id):
                    voice.play(self.players[ctx.channel.id], after=play_note)
                    asyncio.run_coroutine_threadsafe(create_music(index), self.bot.loop)
                else: print('stop')

        play_note(None)

        return await ctx.send(('**You are playing π !** How is it possible ? 0 is a note, 1 an other, 2 an other... etc !'
                               'So yes, this music is π, and it will continue for years ! (ofc not, the bot will crash before)\n'
                               '*pi po ping ping pong pi pi po...*'))

    @commands.command()
    @commands.bot_has_permissions(send_messages=True)
    async def stop(self, ctx):
        user_voice = ctx.author.voice
        if not user_voice:  # si l'utilisateur n'est pas connecté à un salon vocal
            return await ctx.send('Please first join a voice channel :)')

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        print(voice)

        if not voice:
            return await ctx.send("Hm.. I'm not playing anything !")

        self.players.pop(ctx.channel.id, None)
        voice.stop()
        await voice.disconnect()

        await ctx.send("Not patient enough to wait for the music to end?")


def setup(bot: PiBot):
    bot.add_cog(PiMusic(bot))
