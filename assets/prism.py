# Prism Rewrite - Main Prism File
# Contains all the functions that Prism needs to operate

# Last revision on August 7th, 2020.


# Modules
import discord
from random import choice

from asyncio import sleep
from os import system, name

from json import loads, dumps
from operator import itemgetter

from discord.ext import commands, tasks
from Levenshtein.StringMatcher import StringMatcher

# Classes
class BotInstance:

  def create():
    
    global bot
    
    bot = commands.Bot(
        command_prefix = Tools.get_prefix,
        case_insensitive = True,
        owner_ids = [
          633185043774177280,
          666839157502378014,
          403375652755079170
        ]
    )
    
    bot.remove_command("help")

    return bot
  
class Events:

  def on_ready():

    if name == "nt":

      system("cls")

    else:

      system("clear")

    print(f"Logged in as {bot.user}.")
    
    print(f"-------------{'-' * len(str(bot.user))}-")
    
    print()
    
    constant = loads(open("db/guilds", "r").read())

    data = loads(open("db/guilds", "r").read())
    
    for server in constant:
        
      if not bot.get_guild(int(server)):
          
        data.pop(server)
            
    for server in bot.guilds:
        
      if not str(server.id) in constant:
            
        data[str(server.id)] = Constants.guild_preset
    
    open("db/guilds", "w").write(dumps(data, indent = 4))

    data = loads(open("db/users", "r").read())

    for user in data:

      if "protected" in data[user]["data"]["tags"]:

        data[user]["data"]["tags"].remove("protected")

    open("db/users", "w").write(dumps(data, indent = 4))

    try:

      return Tools.status_change.start()
    
    except:

      pass

  async def error_handler(ctx, error):

    if ctx.guild.id in [264445053596991498]:

      return

    elif isinstance(error, commands.BadArgument):
        
      return await ctx.send(embed = Tools.error("Unknown (or invalid) argument provided."))
        
    elif isinstance(error, commands.CommandNotFound):

      return await ctx.send(embed = Tools.error("Sorry, but that command doesn't exist."))

    elif isinstance(error, commands.NotOwner):

      return await ctx.send(embed = Tools.error("This command is owner-only."))

    elif isinstance(error, commands.MissingPermissions):

      return await ctx.send(embed = Tools.error(f"You need the {str(error).split('sing ')[1].split(' per')[0]} permission(s) to use this command."))

    elif "Forbidden: 403 Forbidden" in str(error):
      
      try:

        return await ctx.send(embed = Tools.error("I'm either missing permission(s) or that user is higher than me."))

      except:

        pass

    await ctx.send(embed = Tools.error("Sorry, an unknown error occured."))
      
    return print(f"Command `{ctx.message.content}` used by `{ctx.author}`:" + "\n\t" + str(error))
      
  async def on_message(message):

    ctx, user, db, gdb = message.channel, message.author, loads(open("db/users", "r").read()), loads(open("db/guilds", "r").read())
      
    if user.bot:
          
      return
      
    elif not message.guild:
          
      return await ctx.send("Sorry, Prism isn't available in private messages.")
      
    elif ctx.id == 729760209223942165:

      update = {
        "jumpurl": message.jump_url,
        "content": message.content
      }

      open("assets/res/plain-text/update.txt", "w+").write(dumps(update, indent = 4))

    try:

      prefix = gdb[str(message.guild.id)]["prefix"]

    except:

      return

    # Leveling
    if str(message.author.id) in db:

      levels = db[str(user.id)]["data"]["levels"]

      current_level = levels["level"]
      experience = levels["xp"]

      required_xp = current_level * 1000

      if experience >= required_xp:

        levels["xp"] = 0

        levels["level"] += 1

        open("db/users", "w").write(dumps(db, indent = 4))

        if "levels-enabled" in gdb[str(message.guild.id)]["tags"]:

          await ctx.send(f"> Congratulations, {message.author.mention}! You advanced to level {current_level + 1} :tada:\n> (you can disable these by using ``{prefix}settings levels off``)")

      else:

        levels["xp"] += 5

        open("db/users", "w").write(dumps(db, indent = 4))

    try:

      if not Tools.ensure_command(gdb, message):
          
        return
      
    except:

      pass

    if not str(user.id) in db:
          
      db[str(user.id)] = Constants.user_preset
          
      open("db/users", "w").write(dumps(db, indent = 4))
      
    elif Tools.has_flag(db, user, "blacklisted"):

      return await ctx.send(embed = discord.Embed(title = "Sorry, but you are blacklisted from Prism.", color = 0x126bf1))
      
    elif db[str(user.id)]["balance"] < 0:
          
      db[str(user.id)]["balance"] = 0

    command = message.content.split(prefix)[1]

    if " " in message.content:

      command = command.split(" ")[0]

    if not command in db[str(user.id)]["data"]["commands"]["used"]:

      db[str(user.id)]["data"]["commands"]["used"][command] = 0

    db[str(user.id)]["data"]["commands"]["used"][command] += 1

    db[str(user.id)]["data"]["commands"]["sent"] += 1

    open("db/users", "w").write(dumps(db, indent = 4))

    return True
  
  def guild_add(guild):
    
    db = loads(open("db/guilds", "r").read())

    db[str(guild.id)] = Constants.guild_preset

    return open("db/guilds", "w").write(dumps(db, indent = 4))

  def guild_remove(guild):
    
    db = loads(open("db/guilds", "r").read())

    db.pop(str(guild.id))

    return open("db/guilds", "w").write(dumps(db, indent = 4))

  async def member_joined(member):

    db = loads(open("db/guilds", "r").read())
    
    if db[str(member.guild.id)]["data"]["joinleave_channel"]:
        
      channel = bot.get_channel(int(db[str(member.guild.id)]["data"]["joinleave_channel"]))
        
      embed = discord.Embed(description = f"Welcome to the server, {member.name}; hope you like it here.", color = 0x126bf1)
        
      embed.set_author(name = " | Member Joined", icon_url = bot.user.avatar_url)
        
      embed.set_footer(text = f"Enjoy the server, {member.name}.", icon_url = member.avatar_url)
        
      try:
      
        await channel.send(embed = embed)
      
      except:
          
        db[str(member.guild.id)]["data"]["joinleave_channel"] = None

        open("db/guilds", "w").write(dumps(db, indent = 4))

    if db[str(member.guild.id)]["data"]["autorole"]:

      id = db[str(member.guild.id)]["data"]["autorole"]

      role = discord.utils.get(member.guild.roles, id = id)
          
      if not role:

        db[str(member.guild.id)]["data"]["autorole"] = None

        return open("db/guilds", "w").write(dumps(db, indent = 4))

      try:

        await member.add_roles(role)

      except:

        db[str(member.guild.id)]["data"]["joinleave_channel"] = None

        return open("db/guilds", "w").write(dumps(db, indent = 4))

  async def member_left(member):

      db = loads(open("db/guilds", "r").read())
      
      if db[str(member.guild.id)]["data"]["joinleave_channel"]:
        
        channel = bot.get_channel(int(db[str(member.guild.id)]["data"]["joinleave_channel"]))
        
        embed = discord.Embed(description = f"Sorry to see you go, {member.name}. Enjoy the rest of Discord.", color = 0x126bf1)
        
        embed.set_author(name = " | Member Left", icon_url = bot.user.avatar_url)
        
        embed.set_footer(text = f"Please nobody else leave :C.", icon_url = member.avatar_url)
        
        try:
        
          return await channel.send(embed = embed)
        
        except:
            
          db[str(member.guild.id)]["data"]["joinleave_channel"] = None

          return open("db/guilds", "w").write(dumps(db, indent = 4))

  def message_delete(message):

    if len(message.content) > 409:

      return

    db = loads(open("db/guilds", "r").read())

    if len(db[str(message.guild.id)]["data"]["deleted_messages"]) == 5:

      db[str(message.guild.id)]["data"]["deleted_messages"] = db[str(message.guild.id)]["data"]["deleted_messages"][1:]

    db[str(message.guild.id)]["data"]["deleted_messages"].append(f"{message.author.mention}: {message.content}")

    return open("db/guilds", "w").write(dumps(db, indent = 4))

class Tools:
  
  """

    Helpful tools that Prism uses on a regular basis.

    Import via:
      from assets.prism import Tools

  """

  def has_flag(db, user, flag):

    user_flags = db[str(user.id)]["data"]["tags"]

    if not flag in user_flags:

      return False

    return True

  def ensure_command(gdb, msg):
      
    if msg.content.startswith(gdb[str(msg.guild.id)]["prefix"]):

      return True
  
    return False
  
  def get_prefix(bot, msg):
      
    return loads(open("db/guilds", "r").read())[str(msg.guild.id)]["prefix"]
  
  def uppercase(text):
      
    return text[0].upper() + text[1:]
  
  @tasks.loop(minutes = 15)
  async def status_change():
    
    watching_names = [
      "for p!help.",
      "your mother.",
      "the simpsons.",
      "TV, so shush!",
      f"{len(bot.users)} users.",
      "YouTube.",
      "my many fans.",
      "your father. >_>",
      "strange errors.",
      "for p!rob.",
      "for p!bomb",
      "DmmD code.",
      "commuter sleep.",
      "p!help mod."
    ]
    
    playing_names = [
      "Minecraft.",
      "ROBLOX.",
      "BeamNG.drive.",
      "on an old Atari.",
      "with my dev.",
      "with my many friends.",
      "GTA V.",
      "on steam.",
      "Unturned.",
      "with Dmot.",
      "with Bob.",
      "with your mum. HA!",
    ]
    
    activity = choice(["watching", "playing"])
    
    if activity == "watching":
        
      while True:
      
        try:
            
          await bot.change_presence(status = discord.Status.idle, activity = discord.Activity(type = discord.ActivityType.watching, name = choice(watching_names)))
    
          break
    
        except:
            
          await sleep(15)
        
    else:
        
      while True:
            
        try:
                
          await bot.change_presence(status = discord.Status.idle, activity = discord.Activity(type = discord.ActivityType.playing, name = choice(playing_names)))
        
          break
        
        except:
                
          await sleep(15)

  def error(text):

    embed = discord.Embed(description = f"<:rename_it:730915977742778368> \t **{text}**", color = 0xff0000)

    return embed

  def bought(name, amount):

    embed = discord.Embed(description = f":ballot_box_with_check: **You have just bought {amount} {name}(s).**", color = 0x126bf1)

    return embed

  def getClosestUser(ctx, user, return_member = False):

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

        matcher.set_seqs(user, member[item])

        data[item] = matcher.ratio()

      data["_id"] = member["id"]

      userdata.append(data)

    matches = {}

    for user in userdata:

      for key in user:

        if key != "_id":

          if user[key] > .6:

            matches[user["_id"]] = user[key]

            break

    if not matches:

      return None

    id = int(max(matches.items(), key = itemgetter(1))[0])

    if not return_member:

      return bot.get_user(id)

    return ctx.guild.get_member(id)

class Constants:
  
  alphabet = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
  
  user_preset = {
    "balance": 250,
    "bank": {
      "balance": 0,
      "data": None
    },
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
      "autorole": None
    }
  }

  word_list = [
    "discord", "cat", "dog", "minecraft", "hairnet", "code", "random", "snake", "screen",
    "television", "lottery", "premium", "badge", "roblox", "mouse", "keyboard", "tablet"
  ]

class Cooldowns:

  cooldowns = {}
  
  async def set_cooldown(ctx, name, sec):

      db = loads(open("db/users", "r").read())

      if "Cooldown Repellent" in db[str(ctx.author.id)]["data"]["inventory"]:

        return

      try:

        id = str(ctx.author.id)

        if Tools.has_flag(db, ctx.author, "premium"):

          sec = round(sec / 2)

        cooldowns = Cooldowns.cooldowns

        if not id in cooldowns:
            
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

      except:
        
        pass
          
  def on_cooldown(ctx, name):
      
      id = str(ctx.author.id)
      
      cooldowns = Cooldowns.cooldowns
      
      if not id in cooldowns:
          
        return False
      
      for cooldown in cooldowns[id]:
        
        if name in cooldown:
            
          return True
    
      return False

  def cooldown_text(ctx, name):
      
      id = str(ctx.author.id)
      
      cooldowns = Cooldowns.cooldowns
      
      x = 0
      
      seconds = None
      
      timeframe = None
      
      while x < len(cooldowns[id]):
          
        if name in cooldowns[id][x]:
            
          seconds = cooldowns[id][x][name]
          
          timeframe = "seconds"
          
          break
        
        x += 1
        
      if seconds >= 60:
          
          if seconds >= 3600:
              
            seconds = round(seconds / 3600)
            
            timeframe = "hours"
            
          else:
              
            seconds = round(seconds / 60)
        
            timeframe = "minutes"
              
      return Tools.error(f"Cooldown: You have {seconds} {timeframe}(s) left.")

  def clear_cooldown(user):

    id = str(user.id)

    cooldowns = Cooldowns.cooldowns

    if not id in cooldowns:

      return

    return cooldowns.pop(id)