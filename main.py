# Prism Discord Bot - Rewrite Edition
# The only bot you will ever need.

# Last revision: December 2nd, 2020.
# Copyright 2020-20xx MIT; Benjamin O'Brien.


# Modules
from os import getenv, listdir
from dotenv import load_dotenv
from assets.prism import Bot, Events

# Initialization
load_dotenv()
bot = Bot()

# Commands
for command_folder in listdir("commands"):
    for command in listdir(f"commands/{command_folder}"):
        if command.endswith(".py"):
            bot.load_extension(f"commands.{command_folder}.{command[:-3]}")

# Special extensions
bot.load_extension("assets.cogs.top")

# Bot events
@bot.event
async def on_ready():
    return Events.on_ready()

@bot.event
async def on_command_error(ctx, error):
    return await Events.error_handler(ctx, error)

@bot.event
async def on_message(msg):
    if await Events.on_message(msg) is not True:
        return

    return await bot.process_commands(msg)

@bot.event
async def on_guild_join(guild):
    return Events.guild_add(guild)

@bot.event
async def on_guild_remove(guild):
    return Events.guild_remove(guild)

@bot.event
async def on_member_join(member):
    return await Events.member_joined(member)

@bot.event
async def on_member_remove(member):
    return await Events.member_left(member)

@bot.event
async def on_message_delete(message):
    return Events.message_delete(message)

# Discord connection
bot.run(getenv("BOT_TOKEN"), reconnect = True)
