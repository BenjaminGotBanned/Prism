#  _____      _                 _____                    _ _         ______    _ _ _   _
# |  __ \    (_)               |  __ \                  (_) |       |  ____|  | (_) | (_)
# | |__) | __ _ ___ _ __ ___   | |__) |_____      ___ __ _| |_ ___  | |__   __| |_| |_ _  ___  _ __
# |  ___/ '__| / __| '_ ` _ \  |  _  // _ \ \ /\ / / '__| | __/ _ \ |  __| / _` | | __| |/ _ \| '_ \
# | |   | |  | \__ \ | | | | | | | \ \  __/\ V  V /| |  | | |_  __/ | |____ (_| | | |_| | (_) | | | |
# |_|   |_|  |_|___/_| |_| |_| |_|  \_\___| \_/\_/ |_|  |_|\__\___| |______\__,_|_|\__|_|\___/|_| |_|
#
# This file contains all the functions (and events) that Prism needs to operate.
# The last revision was on November 21st, 2020.
#
# Please note that this is by no means my best work. This is when I still decided to use JSON as my database.
# Since it would be way too time-consuming to make a rewrite in SQLite, I decided to stick with JSON.
#
# It is also worth noting that this file has been improvised by flake8 multiple times, mainly
# due to whitespace issues but a lot more has been fixed as well.
#
# I don't work on this project very much anymore since school started and has been taking up lots of my time.
# If you're interested, feel free to fork this project and do whatever you want.
#
# It isn't discouraged, in fact I would love for somebody to work on this.
#
# Well, thanks for reading!
# -iiPython#0768 (Benjamin)


# Modules
import discord
from sys import argv

from random import choice
from asyncio import sleep

from .logging import Logging
from datetime import datetime

from json import loads, dumps
from os import system, listdir

from operator import itemgetter
from discord.ext import commands, tasks

from .functions import clear, server_check
from Levenshtein.StringMatcher import StringMatcher

# Bot creation
def Bot():

  global log, bot

  log = Logging()  # might as well setup logging too

  bot = commands.Bot(
    command_prefix = Tools.get_prefix,
    case_insensitive = True,
    owner_ids = [
      633185043774177280,
      666839157502378014
    ]
  )

  bot.remove_command("help")  # we replace it with our own

  return bot

# Classes
class Events:

  def on_ready():

    # Nice startup message
    clear()

    print(f"Logged in as {bot.user}.")
    print(f"-------------{'-' * len(str(bot.user))}-")
    print()

    # Basic server checking
    # This insures that a server is registered if it added Prism during a downtime.
    server_check(bot, Constants)

    # Start our 15-minute status changer
    try:
      return Tools.status_change.start()

    except Exception as err:  # I forgot which exception is raised here

      log.warn(f"Status changer exception type: {type(err)}")
      return log.warn("Failed to start the status changer, please do this manually.")

  async def error_handler(ctx, error):

    if isinstance(error, commands.BadArgument):
      return await ctx.send(embed = Tools.error("Unknown (or invalid) argument provided."))
    elif isinstance(error, commands.NotOwner):
      return await ctx.send(embed = Tools.error("This command is owner-only."))
    elif isinstance(error, commands.MissingPermissions):
      return await ctx.send(embed = Tools.error(f"You need the {str(error).split('sing ')[1].split(' per')[0]} permission(s) to use this command."))
    elif isinstance(error, commands.NSFWChannelRequired):
      return await ctx.send(embed = Tools.error("That command is for NSFW channels only."))
    elif isinstance(error, commands.CommandNotFound):
      return
    elif "403" in str(error):
      try: return await ctx.send(embed = Tools.error("Missing permission(s)."))
      except Exception: pass
    elif "NoSuchUser" in str(error):
      return await ctx.send(embed = Tools.error("Couldn't find that user."))

    embed = discord.Embed(title = "Unexpected Error", description = "The command you just used generated an unexpected error.\nPrism has sent an automatic bug report about this problem.\n\nIn the meantime, try some of our other commands. :)", color = 0xFF0000)

    if "--debug" in argv:
      embed.add_field(name = "\nTechnical Information", value = f"```py\n[{type(error)}]: {error}\n```", inline = False)

    try: await ctx.send(embed = embed)
    except Exception: pass

    base = ctx.message.content.split(" ")[0] if " " in ctx.message.content else ctx.message.content
    return log.error(f"Command `{base}` raised an error: {error}")

  async def on_message(message):

    ctx, user, db, gdb = message.channel, message.author, loads(open("db/users", "r").read()), loads(open("db/guilds", "r").read())

    if user.bot: return

    # We aren't in a guild so process it
    if not message.guild:

      command = message.content.lower()
      if not command.startswith("p!"): return

      command = command[2:]

      if " " in command:
        command = command.split(" ")[0]

      if command not in ["ping", "help", "uptime", "invite", "stats", "vote", "eval", "load", "reload"]:
        return await ctx.send(embed = Tools.error("That command can only be used in a guild."))

      return True  # Continue processing the command

    # Fetch prefix
    try:

      prefix = gdb[str(message.guild.id)]["prefix"]

    except KeyError:  # KeyError since flake8 hates bare exceptions

      gdb[str(message.guild.id)] = Constants.guild_preset
      prefix = "p!"
      open("db/guilds", "w").write(dumps(gdb, indent = 4))

    # Triggers
    if message.content in gdb[str(message.guild.id)]["data"]["triggers"]:
      return await ctx.send(gdb[str(message.guild.id)]["data"]["triggers"][message.content])

    # Leveling
    if str(message.author.id) in db:

      levels = db[str(user.id)]["data"]["levels"]

      current_level = levels["level"]
      experience = levels["xp"]

      required_xp = current_level * 250

      # Leveling up
      if experience >= required_xp:

        levels["xp"] = 0

        levels["level"] += 1

        open("db/users", "w").write(dumps(db, indent = 4))

        # Send the level up notification
        if "levels-enabled" in gdb[str(message.guild.id)]["tags"]:

          try: await ctx.send(f"> Congratulations, {message.author.mention}! You advanced to level {current_level + 1} :tada:\n> (you can disable these by using ``{prefix}settings levels off``)")
          except Exception: pass  # This can error for multiple reasons

      else:

        # 5 xp per message
        levels["xp"] += 5
        open("db/users", "w").write(dumps(db, indent = 4))

    # Not a valid command
    if not Tools.ensure_command(gdb, message):

      return

    elif not str(user.id) in db:

      db[str(user.id)] = Constants.user_preset

      open("db/users", "w").write(dumps(db, indent = 4))

    # Blacklist validation
    if Tools.has_flag(db, user, "blacklisted"):

      return await ctx.send(embed = discord.Embed(title = "Sorry, but you are blacklisted from Prism.", color = 0xFF0000))

    # Stop negative balances
    if db[str(user.id)]["balance"] < 0:

      db[str(user.id)]["balance"] = 0

    command = message.content.split(prefix)[1]

    if " " in message.content:

      command = command.split(" ")[0]

    exists = False

    for command_folder in listdir("commands"):

      for _ in listdir(f"commands/{command_folder}"):

        if _ != "__pycache__" and _.replace(".py", "") == command:

          exists = True

    # Log the command to our user profile (if it exists)
    if exists:

      if command not in db[str(user.id)]["data"]["commands"]["used"]:
        db[str(user.id)]["data"]["commands"]["used"][command] = 0

      db[str(user.id)]["data"]["commands"]["used"][command] += 1
      db[str(user.id)]["data"]["commands"]["sent"] += 1

    open("db/users", "w").write(dumps(db, indent = 4))

    return True

  def guild_add(guild):

    """The function you should call whenever Prism is added to a guild"""

    db = loads(open("db/guilds", "r").read())

    db[str(guild.id)] = Constants.guild_preset

    return open("db/guilds", "w").write(dumps(db, indent = 4))

  def guild_remove(guild):

    """The function you should call whenever Prism is removed from a guild."""

    db = loads(open("db/guilds", "r").read())

    db.pop(str(guild.id))

    return open("db/guilds", "w").write(dumps(db, indent = 4))

  async def member_joined(member):

    """This function represents when a member joins a server, it will automatically send a join message."""

    db = loads(open("db/guilds", "r").read())

    if db[str(member.guild.id)]["data"]["joinleave_channel"]:

      channel = bot.get_channel(int(db[str(member.guild.id)]["data"]["joinleave_channel"]))

      embed = discord.Embed(description = f"Welcome to {member.guild.name}, {member.name}.", color = 0x126bf1)
      embed.set_author(name = " | Welcome", icon_url = bot.user.avatar_url)
      embed.set_footer(text = f"Enjoy the server, {member.name}.", icon_url = member.avatar_url)

      try:

        await channel.send(embed = embed)

      except Exception:  # Exception is basically a placeholder for discord.Exceptions.Forbidden

        # We don't have permission to send to that channel
        db[str(member.guild.id)]["data"]["joinleave_channel"] = None
        open("db/guilds", "w").write(dumps(db, indent = 4))

    # Configure autorole for the member
    if db[str(member.guild.id)]["data"]["autorole"]:

      id = db[str(member.guild.id)]["data"]["autorole"]
      role = discord.utils.get(member.guild.roles, id = id)

      if not role:

        # The role was invalid or broken
        db[str(member.guild.id)]["data"]["autorole"] = None
        return open("db/guilds", "w").write(dumps(db, indent = 4))

      try:

        await member.add_roles(role)

      except Exception:  # Again, Exception is a placeholder

        # We don't have permission to add the role either
        db[str(member.guild.id)]["data"]["autorole"] = None
        return open("db/guilds", "w").write(dumps(db, indent = 4))

  async def member_left(member):

    """This function represents when a member leaves a server, it will also automatically send a leave message."""

    db = loads(open("db/guilds", "r").read())

    if db[str(member.guild.id)]["data"]["joinleave_channel"]:

      channel = bot.get_channel(int(db[str(member.guild.id)]["data"]["joinleave_channel"]))

      embed = discord.Embed(description = f"Sorry to see you go, {member.name}. Enjoy the rest of Discord.", color = 0x126bf1)
      embed.set_author(name = " | Member Left", icon_url = bot.user.avatar_url)
      embed.set_footer(text = f" | New user count: {len(member.guild.members)}", icon_url = member.guild.icon_url)

      try:

        return await channel.send(embed = embed)

      except Exception:  # Lots of placeholders, am I right?

        db[str(member.guild.id)]["data"]["joinleave_channel"] = None

        return open("db/guilds", "w").write(dumps(db, indent = 4))

  def message_delete(message):

    if len(message.content) > 100: return
    elif not message.guild: return
    elif not message.content: return

    db = loads(open("db/guilds", "r").read())
    msgs = db[str(message.guild.id)]["data"]["deleted_messages"]

    if len(msgs) == 10:
      msgs = msgs[1:]

    msgs.append({
      "author": str(message.author),
      "date": str(datetime.now().strftime("%D %H:%M:%S")) + " CST",
      "content": message.content
    })

    return open("db/guilds", "w").write(dumps(db, indent = 4))

class Tools:

  """

    Helpful tools that Prism uses on a regular basis.

    Import via:
      from assets.prism import Tools

  """

  def has_flag(db, user, flag):

    user_flags = db[str(user.id)]["data"]["tags"]

    if flag not in user_flags:

      return False

    return True

  def ensure_command(gdb, msg):

    if msg.content.startswith(gdb[str(msg.guild.id)]["prefix"]):

      return True

    return False

  def get_prefix(bot, msg):

    db = loads(open("db/guilds", "r").read())

    if not msg.guild:

      return "p!"

    return db[str(msg.guild.id)]["prefix"]

  def uppercase(text):

    return text[0].upper() + text[1:]

  @tasks.loop(minutes = 15)
  async def status_change():

    watching_names = [
      "for p!help.",
      "TV, so shush!",
      f"{len(bot.users)} users.",
      "YouTube.",
      "my many fans.",
      "for p!rob.",
      "for p!bomb",
      "DmmD code.",
      "p!help mod.",
      "paint dry.",
      "popcorn pop."
    ]

    playing_names = [
      "Minecraft.",
      "ROBLOX.",
      "BeamNG.drive.",
      "on an old Atari.",
      "with my friends.",
      "GTA V.",
      "on steam.",
      "Unturned.",
      "Terraria",
      "with Dmot.",
      "with TDmot.",
      "with Bob.",
      "Astroneer.",
      "Among Us.",
      "Don't Starve."
    ]

    activity = choice(["watching", "playing"])

    while True:

      try:

        if activity == "watching": await bot.change_presence(
          status = discord.Status.idle,
          activity = discord.Activity(
            type = discord.ActivityType.watching,
            name = choice(watching_names)
          )
        )
        else: await bot.change_presence(
          status = discord.Status.idle,
          activity = discord.Activity(
            type = discord.ActivityType.playing,
            name = choice(playing_names)
          )
        )

        break

      except Exception: await sleep(15)  # Retry later

  def error(text):

    embed = discord.Embed(description = f":x: \t **{text}**", color = 0xFF0000)

    return embed

  def bought(name, amount):

    embed = discord.Embed(description = f":ballot_box_with_check: **You have just bought {amount} {name}(s).**", color = 0x126bf1)

    return embed

  async def getClosestUser(ctx, user, return_member = False):

    # Thanks to discord's new intent system, this entire function is broken if you are not verified.
    # Because of this, we migrated back to discord.User, which is what this now returns.
    return user

    user = str(user).lower()

    matcher = StringMatcher()

    userdata = []

    for _user in ctx.guild.members:

      member = {
        "name": _user.name,
        "fullname": _user.name + "#" + str(_user.discriminator),
        "mention": "<@!" + str(_user.id) + ">",
        "nickname": _user.display_name,
        "discriminator": str(_user.discriminator),
        "discrim2": "#" + str(_user.discriminator),
        "id": str(_user.id)
      }

      data = {}

      for item in member:

        matcher.set_seqs(user, member[item].lower())

        data[item] = matcher.quick_ratio()

      data["_id"] = member["id"]

      userdata.append(data)

    matches = {}

    for user in userdata:

      for key in user:

        if key != "_id":

          if user[key] > .5:

            matches[user["_id"]] = user[key]

            break

    if not matches:

      raise ValueError(f"NoSuchUser: {user}")

    id = int(max(matches.items(), key = itemgetter(1))[0])

    if not return_member:

      return bot.get_user(id)

    return ctx.guild.get_member(id)

  async def getBannedUser(ctx, user):

    user = str(user).lower()

    matcher = StringMatcher()

    userdata = []

    for _user in await ctx.guild.bans():

      _user = _user.user

      member = {
        "name": _user.name,
        "fullname": _user.name + "#" + str(_user.discriminator),
        "mention": "<@!" + str(_user.id) + ">",
        "nickname": _user.display_name,
        "discriminator": str(_user.discriminator),
        "discrim2": "#" + str(_user.discriminator),
        "id": str(_user.id)
      }

      data = {}

      for item in member:

        matcher.set_seqs(user, member[item].lower())

        data[item] = matcher.quick_ratio()

      data["_id"] = member["id"]

      userdata.append(data)

    matches = {}

    for user in userdata:

      for key in user:

        if key != "_id":

          if user[key] > .5:

            matches[user["_id"]] = user[key]

            break

    if not matches:

      raise ValueError(f"NoSuchUser: {user}")

    id = int(max(matches.items(), key = itemgetter(1))[0])

    for banned in await ctx.guild.bans():

      if banned.user.id == id:

        return banned.user

class Constants:

  alphabet = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]

  user_preset = {
    "balance": 250,
    "pet": {
      "name": None,
      "level": None,
      "type": None,
      "holding": None,
      "adopted_on": None
    },
    "data": {
      "bio": None,
      "inventory": {},
      "warnings": {},
      "levels": {
        "level": 1,
        "xp": 0,
        "rep": 0,
      },
      "tags": [],
      "commands": {
        "sent": 0,
        "used": {}
      }
    }
  }

  guild_preset = {
    "prefix": "p!",
    "tags": [
      "nsfw-enabled",
      "levels-enabled"
    ],
    "data": {
      "joinleave_channel": None,
      "deleted_messages": [],
      "last_updated": "Never",
      "autorole": None,
      "triggers": {},
      "automod": {}
    }
  }

class Cooldowns:

  """Represents Prism's internal cooldown system."""

  cooldowns = {}

  async def set_cooldown(ctx, name, sec):

    """Takes the context, a command name, the seconds and constructs a cooldown for the message author."""

    db = loads(open("db/users", "r").read())

    if "Cooldown Repellent" in db[str(ctx.author.id)]["data"]["inventory"]:

      sec = round(sec / 2)

    try:

      id = str(ctx.author.id)

      if Tools.has_flag(db, ctx.author, "premium"):

        sec = round(sec / 2)

      cooldowns = Cooldowns.cooldowns

      if id not in cooldowns:

        cooldowns[id] = []

      cooldown = {
        name: sec
      }

      cooldowns[id].append(cooldown)

      counter = 0

      while counter < sec:

        x = 0

        while x < len(cooldowns[id]):

          if name in cooldowns[id][x]:

            cooldowns[id][x][name] -= 1

            break

          x += 1

        await sleep(1)
        counter += 1

      cooldowns[id].pop(x)

      if len(cooldowns[id]) == 0:

        cooldowns.pop(id)

    # This catches so that we can clear cooldowns
    except Exception: pass  # Yet another placeholder, when will they end?

  def on_cooldown(ctx, name):

    """Returns whether the specified user is on cooldown for a specific command"""

    # Just some references
    id = str(ctx.author.id)
    cooldowns = Cooldowns.cooldowns

    # If you don't have any cooldowns, you probably aren't on a cooldown ;)
    if id not in cooldowns: return False

    # Loop through cooldowns
    for cooldown in cooldowns[id]:

      if name in cooldown:

        return True

    return False  # This is better than getting None returned

  def cooldown_text(ctx, name):

    """Takes context, the command name, and will return formatted cooldown text to reply with."""

    # References
    id = str(ctx.author.id)
    cooldowns = Cooldowns.cooldowns

    x = 0
    seconds = None
    timeframe = None

    # Loop through our cooldowns
    while x < len(cooldowns[id]):

      # Located our cooldown
      if name in cooldowns[id][x]:

        seconds = cooldowns[id][x][name]
        timeframe = "seconds"

        break

      x += 1  # Proceed with loop

    # Time formatting (there is probably a better way of doing this)
    if seconds >= 60:

        # Just kidding, this is hours
        if seconds >= 3600:
          seconds = round(seconds / 3600)
          timeframe = "hours"

        else:

          # uno reverse card its actually minutes
          seconds = round(seconds / 60)
          timeframe = "minutes"

    # Fantastic error embed
    return Tools.error(f"Cooldown: You have {seconds} {timeframe}(s) left.")

  def clear_cooldown(user):

    """Takes a user and clears all of their cooldowns."""

    # References
    id = str(user.id)
    cooldowns = Cooldowns.cooldowns

    # Simple error protection
    if id not in cooldowns: return

    # Bam, removed it from the cooldowns
    return cooldowns.pop(id)
