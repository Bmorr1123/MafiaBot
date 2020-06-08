import discord, os, json, asyncio
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
            "guilds": {

            },
            "players": {

            },
        }
        self.guilds = []
        # Load a list of guild ids that have setup Mafia
        for guild in os.listdir("guilds"):
            print(guild)
            self.guilds.append(guild)

    def is_queue_channel(self, channel):
        for guild in self.data["guilds"]:
            if channel.id == guild["queue"]:
                return True
        return False

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Check if Mafia
        if not (before.channel.guild.id in self.guilds or after.channel.guild.id in self.guilds):
            return

        print(f"{member} updated their voice state in a mafia server.")
        # Check if moved in
        if self.is_queue_channel(after.channel):
            channel = after.channel
            if len(channel.members) == channel.user_limit:
                # TODO: Create a new game here!
                pass

    @commands.group()
    async def mafia(self, ctx):
        """All mafia related commands"""
        if ctx.invoked_subcommand is None:
            await self.bot.say("Invalid sub command passed.")

    @mafia.command()
    @commands.has_permissions(manage_guild=True)
    async def setup(self, ctx):
        guild = ctx.guild
        # Cat/Channel creation
        rlm_category = discord.utils.find(lambda cat: cat.name == "Rocket League Mafia", guild.categories)
        if rlm_category is None:
            rlm_category = await guild.create_category("Rocket League Mafia")
        rlm_queue = discord.utils.get(rlm_category.channels, name="Mafia Queue", type=discord.ChannelType.voice)
        if rlm_queue is None:
            rlm_queue = await guild.create_voice_channel('Mafia Queue', category=rlm_category)
        await rlm_queue.edit(user_limit=6)

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

    def load_guild(self, guild):
        json_path = os.path.join("guilds", guild.id)
        if not os.path.exists(json_path):
            self.data["guilds"][guild.id] = {}
        with open(json_path) as guild_json:
            data = json.load(guild_json)
            json.dumps(data, sort_keys=True, indent=4)
            self.data["guilds"][guild.id] = data

    def unload_guild(self, guild):
        json_path = os.path.join("guilds", guild.id)
        with open(json_path, "w+") as guild_json:
            json.dump(self.data["guilds"][guild.id], guild_json, sort_keys=True, indent=4)
        self.data["guilds"].pop(guild.id)


class Game:
    def __init__(self, guild, *players):
        pass
