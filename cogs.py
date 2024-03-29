import asyncio
import discord
from random import shuffle
from discord.ext import commands

games = []
class Default(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in and listening as {self.bot.user}!")
        await self.bot.change_presence(activity=discord.Game(name="Rocket League Mafia"))  # Set Discord status

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author == self.bot.user:
            return
        if 'hello' in ctx.content.lower():
            await ctx.channel.send("Hello!")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, arg: int):
        messages = await ctx.channel.history(limit=arg).flatten()
        for message in reversed(messages):
            await message.delete()


class Mafia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = []

    @commands.group()
    async def mafia(self, ctx):
        """All mafia related commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid sub command passed.")

    def is_queue_channel(self, channel):
        if channel is None:
            return False
        if channel.name == "Mafia Queue":
            return True
        return False

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Check if Mafia
        if before.channel is None:
            pass
        elif before.channel.name.startswith("Mafia Game Room"):
            if len(before.channel.members) == 0:
                await before.channel.delete()
        if after.channel is None or after.channel.name != "Mafia Queue":
            return
        print(f"{member} updated their voice state in a mafia server.")
        # Check if moved in
        if self.is_queue_channel(after.channel):
            channel = after.channel
            if len(channel.members) == channel.user_limit:
                await self.create_game(channel)

    @mafia.command()
    async def help(self, ctx):
        await ctx.message.delete()  # Delete player message

        #  Send message
        await ctx.send(f"Use ?mafia report \'team\' to report game winner. Ex. ?mafia report blue\n"
                       f"Then react to the player who corresponds to your guess for the mafia.")

    @mafia.command()
    async def rules(self, ctx):
        await ctx.message.delete()  # Delete player message

        #  Send rules message
        await ctx.send(f"To Start, everyone must go into the Mafia Queue channel. "
                 f"Once it is full, those members will be automatically moved into a voice "
                 f"channel and a text channel will be created. Each player will also be DMed "
                 f"with their team and role for the round. The goal of the mafia is to lose game without being caught "
                 f"throwing.\n\nAfter the Rocket League match is played, one person "
                 f"must report the team who won in the text channel using ?mafia report "
                 f"winning_team.\n\nThen, each player must guess who the mafia is using ?mafia guess "
                 f"username. Once each player, including the mafia, has guessed, each player who "
                 f"correctly guessed who the mafia was will be awarded 1 point. If no one guesses "
                 f"who the mafia is and the mafia\'s team loses, the mafia will be awarded 3 "
                 f"points.\n\nWhichever player has the most points at the end of 5 rounds wins.")

    @mafia.command()
    async def report(self, ctx, arg):

        if ctx.channel.name != "mafia-text-room":
            await ctx.message.delete()
            return

        game = None
        for g in self.games:
            if ctx.channel == g.text_channel:
                game = g
                break

        if arg.lower() == "blue":
            game.round_winner = "Blue"
        elif arg.lower() == "orange":
            game.round_winner = "Orange"
        else:
            await ctx.message.delete()
            return

        if game.round_winner.lower() == "blue" or game.round_winner.lower() == "orange":
            plrs = ""
            reactions = "🇦 🇧 🇨 🇩 🇪 🇫".split(" ")
            for i, player in enumerate(game.players):
                plrs += f"{reactions[i]} – {player.name}\n"
            msg = await ctx.send(f"{plrs}")
            game.voting_message = msg
            for _g in range(len(game.players)):
                await msg.add_reaction(reactions[_g])

    def _get_emoji(self, emoji):
        for i, reaction in enumerate("🇦 🇧 🇨 🇩 🇪 🇫".split(" ")):
            if emoji in reaction or reaction in emoji:
                return i
        return -1

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        if self.bot.get_channel(payload.channel_id).name != "mafia-text-room" or self._get_emoji(payload.emoji.name) <\
                0 or "mafia" in self.bot.get_user(payload.user_id).name.lower():
            return
        else:
            channel = self.bot.get_channel(payload.channel_id)

        game = None
        for g in self.games:
            if self.bot.get_channel(payload.channel_id) == g.text_channel:
                game = g
                break

        if payload.message_id != game.voting_message.id:
            return

        for player in game.players:
            if player.name == payload.member.name:
                if player.name == game.players[self._get_emoji(payload.emoji.name)].name:  # If the player picks themself
                    await channel.send(f"You can\'t pick yourself, {self.bot.get_user(payload.user_id).name}.")
                elif player.guess is not None:  # If player already made a guess
                    await channel.send(f"{self.bot.get_user(payload.user_id)}, you have already guessed this round.")
                elif str(self._get_emoji(payload.emoji.name)) in "0 1 2 3 4 5".split(" "):  # If player is correctly picked
                    player.guess = self._get_emoji(payload.emoji.name)

        all_guessed = True
        mafia, mafia_name, mafia_obj = None, None, None
        for i, player in enumerate(game.players):
            if player.guess is None:
                all_guessed = False
            if player.role == "Mafia":
                mafia = i
                mafia_name = player.name
                mafia_obj = player

        if all_guessed:
            await self.bot.get_channel(payload.channel_id).send(f"{mafia_name} was the Mafia!")  # Send message on who was the mafia
            game.round += 1
            game.round_winner = None

            mafia_guessed = 0
            for player in game.players:
                if player.guess == mafia:
                    print(f"{player.name} got a point!")
                    player.score += 1
                    mafia_guessed += 1

            if mafia_guessed == 0:
                mafia_obj.score += 3

            if game.round == game.total_rounds:  # If all the rounds of the game have been played
                # Print out player scores
                scoreboard = "```\n"
                for player in self.sort_player_scores(game.players):
                    scoreboard += f"{player.name} - {player.score}\n"
                scoreboard += "```"
                await self.bot.get_channel(payload.channel_id).send(scoreboard)

                self.games.remove(game)  # Remove game from list of games

                await asyncio.sleep(30)  # Wait 30 seconds
                await self.bot.get_channel(payload.channel_id).delete()  # Delete text-channel
            else:  # If there are still rounds to play

                for player in game.players:
                    player.guess = None
                shuffle(game.players)

                blue = game.players[0:len(game.players) // 2]

                shuffle(game.players)
                for i, player in enumerate(game.players):
                    team = "Orange"
                    if player in blue:
                        team = "Blue"
                    player.team = team
                    if i == 0:
                        player.role = "Mafia"
                        await player.obj.send(f"You are the MAFIA!")  # Send DM to mafia
                    else:
                        player.role = None

                await self.msg_teams(game.players, self.bot.get_channel(payload.channel_id))

    @mafia.command()
    async def exit(self, ctx):
        if ctx.channel.name == "mafia-text-room":

            g = None
            for game in self.games:
                if game.text_channel == ctx.channel:
                    g = game
                    break

            if g is not None:
                self.games.remove(g)

            await ctx.channel.delete()

    def sort_player_scores(self, players):
        p = players
        ret = []
        while len(p) > 0:
            highest = p[0]
            for player in p:
                if player.score > highest.score:
                    highest = player
            ret.append(highest)
            p.remove(highest)
        return ret

    async def msg_teams(self, players, text_channel):
        blue, orange = "", ""
        for player in players:
            if player.team.lower() == "blue":
                blue += f"\t{player.name}\n"
            else:
                orange += f"\t{player.name}\n"
        await text_channel.send(f"```\nBlue:\n{blue}\nOrange:\n{orange}```")

    @mafia.command()
    async def guess(self, ctx, arg):

        if ctx.channel.name != "mafia-text-room":
            await ctx.message.delete()
            return

        game = None
        for g in self.games:
            if ctx.channel == g.text_channel:
                game = g
                break

        if game.round_winner is None:
            await ctx.message.delete()
            return

        for player in game.players:
            if player.name == ctx.message.author.name:
                if player.name == arg:  # If the player picks themself
                    await ctx.send("You can\'t pick yourself, dumbass.")
                    return
                elif player.guess is not None:  # If player already made a guess
                    await ctx.send(f"{ctx.message.author}, you have already guessed this round.")
                    return
                elif arg in game.player_names:  # If player is correctly picked
                    player.guess = arg

        all_guessed = True
        mafia = None
        mafia_obj = None
        for player in game.players:
            if player.guess is None:
                all_guessed = False
            if player.role == "Mafia":
                mafia = player.name
                mafia_obj = player

        if all_guessed:
            await ctx.send(f"{mafia} was the Mafia!")  # Send message on who was the mafia
            game.round += 1
            game.round_winner = None

            mafia_guessed = 0
            for player in game.players:
                if player.guess == mafia:
                    player.score += 1
                    mafia_guessed += 1

            if mafia_guessed == 0:
                mafia_obj.score += 3

            if game.round == game.total_rounds:  # If all the rounds of the game have been played
                # Print out player scores
                scoreboard = "```\n"
                for player in self.sort_player_scores(game.players):
                    scoreboard += f"{player.name} - {player.score}\n"
                scoreboard += "```"
                await ctx.send(scoreboard)

                self.games.remove(game)  # Remove game from list of games

                await asyncio.sleep(30)  # Wait 30 seconds
                await ctx.channel.delete()  # Delete text-channel
            else:  # If there are still rounds to play
                for player in game.players:
                    player.guess = None
                shuffle(game.players)

                blue = game.players[0:len(game.players) // 2]

                shuffle(game.players)
                for i, player in enumerate(game.players):
                    team = "Orange"
                    if player in blue:
                        team = "Blue"
                    player.team = team
                    if i == 0:
                        player.role = "Mafia"
                        await player.obj.send(f"You are the MAFIA!")  # Send DM to mafia
                    else:
                        player.role = None
                await self.msg_teams(game.players, ctx)

    async def create_game_channels(self, channel):
        text_overwrites = {
            channel.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        }
        voice_overwrites = {
            channel.guild.default_role: discord.PermissionOverwrite(connect=False),
        }
        voice_channel = await channel.guild.create_voice_channel(
            'Mafia Game Room',
            category=channel.category,
            overwrites=voice_overwrites
        )
        text_channel = await channel.guild.create_text_channel(
            'Mafia-Text-Room',
            category=channel.category,
            overwrites=text_overwrites
        )
        names = ""
        for member in channel.members:
            names += member.name + ", "
            await member.move_to(voice_channel)
            await voice_channel.set_permissions(member, connect=True)
            await text_channel.set_permissions(member, read_messages=True, send_messages=True,
                                               read_message_history=True, add_reactions=True)
        await text_channel.send(f"__Players: {names[0:-2]}__\nUse ?mafia help for help on report syntax.")
        return voice_channel, text_channel

    async def create_game(self, channel):
        player_objects = []
        players = channel.members
        voice, text = await self.create_game_channels(channel)
        shuffle(players)

        blue = players[0:len(players) // 2]

        shuffle(players)
        for i, player in enumerate(players):
            team = "Orange"
            if player in blue:
                team = "Blue"
            if i == 0:
                player_objects.append(Player(player.name, "Mafia", player, team))
                await player.send(f"You are the MAFIA!")
            else:
                player_objects.append(Player(player.name, None, player, team))
        await self.msg_teams(player_objects, text)
        self.games.append(Game(voice, text, player_objects, 5))

    @mafia.command()
    @commands.has_permissions(manage_guild=True)
    async def setup(self, ctx):
        guild = ctx.guild
        # Category/Channel creation
        rlm_category = discord.utils.find(lambda cat: cat.name == "Rocket League Mafia", guild.categories)
        if rlm_category is None:
            rlm_category = await guild.create_category("Rocket League Mafia")
        rlm_queue = discord.utils.get(rlm_category.channels, name="Mafia Queue", type=discord.ChannelType.voice)
        if rlm_queue is None:
            rlm_queue = await guild.create_voice_channel('Mafia Queue', category=rlm_category)
        await rlm_queue.edit(user_limit=6)
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
        await asyncio.sleep(30)
        await bots_message.delete()


class Player:
    def __init__(self, username, role, obj, team):
        self.name = username
        self.role = role
        self.score = 0
        self.guess = None
        self.obj = obj  # Discord member object
        self.team = team

    def __str__(self):
        return f"{self.name} - {self.team} - {self.role}"


class Game:
    def __init__(self, voice_channel, text_channel, players, total_rounds):
        self.voice_channel = voice_channel
        self.text_channel = text_channel
        self.players = players
        self.total_rounds = total_rounds
        self.round = 0
        self.player_names = []
        for p in self.players:  # Creates a list of all usernames of the players
            self.player_names.append(p.name)
        self.round_winner = None
        self.voting_message = None
