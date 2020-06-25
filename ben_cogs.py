import discord, os, json, asyncio, random
from discord.ext import commands


class Default(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in and listening as {self.bot.user}!")

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author == self.bot.user:
            return
        if 'hello' in ctx.content.lower():
            await ctx.channel.send("Hello!")

    @commands.command()
    async def ping(self, ctx):
        await ctx.send('pong')

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, arg: int):
        messages = await ctx.channel.history(limit=arg).flatten()
        for message in reversed(messages):
            await message.delete()


class Mafia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = {
            "guilds": {},
            "players": {},
        }
        # Load a list of guild ids that have setup Mafia
        for guild_id in os.listdir("guilds"):
            print(guild_id)
            self.load_guild(guild_id)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await ctx.send(error)

    @commands.group()
    async def mafia(self, ctx):
        """All mafia related commands"""
        if ctx.invoked_subcommand is None:
            await self.bot.say("Invalid sub command passed.")

    def is_queue_channel(self, channel):
        for guild in self.data["guilds"]:
            if channel.id == guild["queue"]:
                return True
        return False

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Check if Mafia
        if not (after.channel and after.channel.name == "Mafia Queue"):
            return
        channel = after.channel
        print(f"{member} updated their voice state in {channel}.")
        # Check if full
        if len(channel.members) == channel.user_limit:
            print("Queue full!")
            await self.run_game(channel)

    async def run_game(self, channel):
        text_overwrites = {
            channel.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        }
        voice_overwrites = {
            channel.guild.default_role: discord.PermissionOverwrite(connect=False),
        }
        voice_channel = await channel.guild.create_voice_channel(
            'Mafia Game',
            category=channel.category,
            overwrites=voice_overwrites
        )
        text_channel = await channel.guild.create_text_channel(
            'mafia_text',
            category=channel.category,
            overwrites=text_overwrites
        )
        for member in channel.members:
            await member.move_to(voice_channel)
            await voice_channel.set_permissions(member, connect=True)
            await text_channel.set_permissions(member, read_messages=True)
        # await game_channel.set_permissons(channel.guild.default_role, )
        pass

    @mafia.command()
    @commands.has_permissions(manage_guild=True)
    async def setup(self, ctx):
        guild = ctx.guild
        # Cat/Channel creation
        print("cat creation")
        rlm_category = discord.utils.find(lambda cat: cat.name == "Rocket League Mafia", guild.categories)
        if rlm_category is None:
            rlm_category = await guild.create_category("Rocket League Mafia")
        print("chat creation")
        rlm_queue = discord.utils.get(rlm_category.channels, name="Mafia Queue", type=discord.ChannelType.voice)
        if rlm_queue is None:
            rlm_queue = await guild.create_voice_channel('Mafia Queue', category=rlm_category)
        await rlm_queue.edit(user_limit=6)
        # Server data creation
        print("data creation")
        if not self.data["guilds"][guild.id]:
            print("doing thing")
            self.data["guilds"][guild.id] = {
                "category": rlm_category.id,
                "queue": rlm_queue.id,
                "mafia_players": [],
            }
        print("message deletion")
        # Message deletion
        bots_message = await ctx.send("Mafia setup complete.")
        await ctx.message.delete()
        await asyncio.sleep(5)
        await bots_message.delete()

    @mafia.command()
    @commands.has_permissions(manage_guild=True)
    async def delete(self, ctx):
        # Deleting Channel
        rlm_category = discord.utils.find(lambda cat: cat.name == "Rocket League Mafia", ctx.guild.categories)
        if rlm_category is not None:
            for channel in rlm_category.channels:
                await channel.delete(reason=f"{ctx.author} ran delete_mafia.")
            await rlm_category.delete(reason=f"{ctx.author} ran delete_mafia.")
        bots_message = await ctx.send("Mafia deleted.")
        # Deleting Message
        await ctx.message.delete()
        await asyncio.sleep(5)
        await bots_message.delete()

    def load_guild(self, guild_id):
        """Returns guild data if saved in the guilds folder, otherwise returns None."""
        json_path = os.path.join("guilds", guild_id)
        if os.path.exists(json_path):
            with open(json_path) as guild_json:
                data = json.load(guild_json)  # Loads json file as python data structure
                json.dumps(data, sort_keys=True, indent=4)  # Prints out guild data for testing.
                self.data["guilds"][guild_id] = data  # Enters guild data into self.data
                return data
        else:
            return None

    def unload_guild(self, guild_id):
        json_path = os.path.join("guilds", guild_id)
        with open(json_path, "w+") as guild_json:
            json.dump(self.data["guilds"][guild_id], guild_json, sort_keys=True, indent=4)
        self.data["guilds"].pop(guild_id)

    def load_player(self, player_id):
        json_path = os.path.join("players", player_id)
        if os.path.exists(json_path):
            with open(json_path) as player_json:
                data = json.load(player_json)  # Loads json file as python data structure
                json.dumps(data, sort_keys=True, indent=4)  # Prints out guild data for testing.
                self.data["players"][player_id] = data  # Enters guild data into self.data
                return data
        else:
            return None

    def unload_player(self, player_id):
        json_path = os.path.join("players", player_id)
        with open(json_path, "w+") as player_json:
            json.dump(self.data["players"][player_id], player_json, sort_keys=True, indent=4)
        self.data["players"].pop(player_id)

    def cog_unload(self):
        print("Unloaded Mafia!")
        for guild_id in self.data["guilds"].keys():
            self.unload_guild(guild_id)
        for player_id in self.data["players"].keys():
            self.unload_player(player_id)


class Game:
    def __init__(self, guild, *players):
        pass
