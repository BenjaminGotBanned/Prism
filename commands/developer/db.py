# Modules
import json
import discord

from os import stat
from datetime import datetime

from assets.prism import Tools
from discord.ext import commands

from os.path import exists, abspath

# Main Command Class
class Database(commands.Cog):

    """
    Handy cog for interacting with the JSON databases
    Last modified on 1/4/2020

    Basic usage:
      p!db users 1234567890.balance 250     Sets the value to 250
      p!db users 1234567890.balance         Reads from the value
      p!db users 1234567890                 Dumps the JSON dictionary containing the user info
    """

    def __init__(self, bot):
        self.bot = bot
        self.desc = "Edits the prism database"
        self.usage = "db <database> <key> [value]"

    def wrap(self, value):
        return f"```\n{value}\n```"

    def set_db_value(self, db, keys, value):

        for key in keys[:-1]:
            db = db.setdefault(key, {})

        db[keys[-1]] = value

    @commands.command()
    @commands.is_owner()
    async def db(self, ctx, database = None, key = None, *, value = None):

        # Check for database
        if database is None:
            return await ctx.send(embed = Tools.error("No database name specified to load."))

        # Load the database
        db_name = "db/" + database
        if not exists(db_name):
            return await ctx.send(embed = Tools.error("The specified database does not exist."))

        with open(db_name) as file:
            db = json.loads(file.read())

        # Check if no key was provided
        if key is None:

            # Summarize the database
            embed = discord.Embed(color = 0x126bf1)

            embed.add_field(name = "Size", value = self.wrap(len(db)), inline = False)
            embed.add_field(name = "Database location", value = self.wrap(abspath(db_name)), inline = False)
            embed.add_field(name = "Last wrote to", value = self.wrap(datetime.fromtimestamp(stat(db_name).st_mtime).strftime("%D")), inline = False)

            # Finish up embed
            embed.set_footer(icon_url = ctx.author.avatar_url, text = f"| Requested by {ctx.author}.")
            return await ctx.send(embed = embed)

        # Identify the key structure
        key_struct = key.split(".")

        # Locate the key path
        path = db
        spath = database

        for s in key_struct:

            try:
                path = path[s]

            except Exception as error:

                # Construct error embed
                embed = discord.Embed(color = 0xFF0000)

                embed.add_field(name = "Python traceback", value = self.wrap(error), inline = False)
                embed.add_field(name = "Current location", value = self.wrap(spath + f" ({type(path).__name__})"), inline = False)
                embed.add_field(name = "Referenced location", value = self.wrap(spath + "." + s), inline = False)

                embed.set_footer(icon_url = ctx.author.avatar_url, text = f"| Requested by {ctx.author}.")
                return await ctx.send(embed = embed)

            spath += "." + s

        # Set value
        if value is not None:

            # Convert value
            try:
                value = json.loads(value)

            except json.JSONDecodeError:

                try:
                    value = json.loads(f"\"{value}\"")

                except json.JSONDecodeError:
                    return await ctx.send(embed = Tools.error("Invalid JSON value provided!"))

            self.set_db_value(db, key_struct, value)

            # Save database
            with open(db_name, "w") as file:
                file.write(json.dumps(db, indent = 4))

        # Construct information embed
        embed = discord.Embed(color = 0x126bf1)

        embed.add_field(name = "Location value", value = self.wrap(json.dumps(path, indent = 2)), inline = False)
        if value is not None:
            embed.add_field(name = "New location value", value = self.wrap(json.dumps(value, indent = 2)), inline = False)

        embed.add_field(name = "Current location", value = self.wrap(spath + f" ({type(path).__name__})"), inline = False)

        # Size info
        try:
            size = len(path)

        except TypeError:
            size = len(str(path))

        embed.add_field(name = "Containing objects", value = self.wrap(size))

        # Finish up embed
        embed.set_footer(icon_url = ctx.author.avatar_url, text = f"| Requested by {ctx.author}.")
        return await ctx.send(embed = embed)

# Link to bot
def setup(bot):
    bot.add_cog(Database(bot))
