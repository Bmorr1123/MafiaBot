from discord.ext import commands
from cogs import *
import json


'''
https://discord.com/api/oauth2/authorize?client_id=714649492036517930&permissions=8&scope=bot

'''


config = {}
with open("config.json", "r") as file:
    for key, value in json.load(file).items():
        config[key] = value


bot = commands.Bot(command_prefix=config["prefix"])

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(error)

cogs = [Default(bot), Mafia(bot)]
for cog in cogs:
    bot.add_cog(cog)
    print(f"Loaded \"{cog.qualified_name}\" cog!")

print(config["token"])
bot.run(config["token"])
