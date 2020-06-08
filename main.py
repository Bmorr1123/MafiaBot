import os, discord, json, asyncio
from cogs import *
from discord.ext import commands

lines = open("config.txt", "r").readlines()
def get_key(key):
    for line in lines:
        if line.startswith(key):
            return line[line.find(":") + 1:].replace("\n", "")


bot = commands.Bot(command_prefix=get_key("prefix"))

@bot.event
async def on_command_error(self, ctx, error):
    await ctx.send(error)

cogs = [Default(bot), Mafia(bot)]
for cog in cogs:
    bot.add_cog(cog)
    print(f"Loaded \"{cog.qualified_name}\" cog!")

bot.run(get_key("token"))
