import discord
from discord.ext import commands
from youtube_dl import YoutubeDL

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.is_playing = False
        self.is_paused = False

        self.queue = []
        self.ytdl_options = {"format": "bestaudio", "noplaylist": "True"}
        self.ffmpeg_options = {"before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", "options": "-vn"}

        self.vc = None

    def yt_search(self, search):
        with YoutubeDL(self.ytdl_options) as ytdl:
            
                info = ytdl.extract_info(f"ytsearch:{search}", download= False)['entries'][0]
            
        return {"source": info['formats'][0]["url"], "title": info["title"]}
    
    async def next_song(self):
        if len(self.queue) > 0:
            self.is_playing = True

            song = self.queue[0][0]['source']

            self.queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(song, **self.ffmpeg_options), after=lambda e: self.next_song())

        else:
            self.is_playing = False
            await self.vc.disconnect()

    async def play_song(self, interaction: discord.Interaction):
        if len(self.queue) > 0:
            self.is_playing = True

            song = self.queue[0][0]['source']

            if self.vc == None or not self.vc.is_connected():
                self.vc = await self.queue[0][1].connect()
                
                if self.vc == None:
                    await interaction.send("Could not join the voice channel")
                    return

            else:
                await self.vc.move_to(self.queue[0][1])

            self.queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(song, **self.ffmpeg_options), after=lambda e: self.next_song())

    @commands.command(name= "play", aliases=["p"], help="Plays a song from youtube")
    async def play(self, interaction: discord.Interaction, *search):
        search_query = " ".join(search)

        vc = interaction.author.voice.channel
        if vc is None:
            await interaction.reply("Connect to a voice channel first")
        elif self.is_paused:
            self.vc.resume()
        else:
            song = self.yt_search(search_query)
            if song == False:
                await interaction.reply("Could not get the song, try a different search")
            else:
                await interaction.send(f"Adding song {song['title']}")
                self.queue.append([song, vc])

                if self.is_playing == False:
                    await self.play_song(interaction)

    @commands.command(name="pause", help="Pauses the currently playing song")
    async def pause(self, interaction: discord.Interaction):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()
            await interaction.send("I paused the song")
        elif self.is_paused:
            await interaction.reply("I am already paused")
        else:
            await interaction.reply("Currently not playing any song")

    @commands.command(name="resume", help="Resumes the current playing song")
    async def resume(self, interaction: discord.Interaction):
        if self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()
            await interaction.send("I resumed the song")
        else:
            await interaction.reply("I am not currently paused")

    @commands.command(name="skip", help="Skips the current playing song")
    async def skip(self, interaction: discord.Interaction):
        if self.vc != None:
            if len(self.queue) > 0:
                self.vc.stop()
                await self.play_song(interaction)
                await interaction.send("I skipped to the next song")
            else:
                await self.leave(interaction)
        else:
            await interaction.reply("You are not in any voice channel")

    @commands.command(name="queue", aliases=["q"], help="Shows a list of songs in queue")
    async def queue(self, interaction: discord.Interaction):
        song_list = "Up Next: \n"

        for no, song in enumerate(self.queue[:5]):
            song_list += str(no+1) + ") " + song[0]["title"] + "\n"

        if song_list != "Up Next: \n":
            await interaction.send(song_list)
        else:
            await interaction.send("No songs in queue")

    @commands.command(name="clear", help="Clears the song queue")
    async def clear(self, interaction: discord.Interaction):
        if self.vc != None and self.is_playing:
            self.vc.stop()
        
        self.queue = []
        await interaction.send("Cleared the song queue")

    @commands.command(name="leave", aliases=["stop", "fuckoff"], help="Disconnects me from the vc")
    async def leave(self, interaction:discord.Interaction):
        if self.vc != None:
            self.is_playing = False
            self.is_paused = False
            await self.vc.disconnect()





async def setup(bot):
    await bot.add_cog(Music(bot))
