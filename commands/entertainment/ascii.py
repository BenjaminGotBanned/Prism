# Modules
from requests import get
from assets.prism import Tools

from discord.ext import commands

# Main Command Class
class Ascii(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    self.desc = "Turns text into ascii art"
    self.usage = "ascii [text]"

  @commands.command()
  async def ascii(self, ctx, *, sentence: str = None):
    
    if not sentence:
      return await ctx.send(embed = Tools.error("No text was specified."))

    for mention in ctx.message.mentions:
      sentence = sentence.replace(f"<@{mention.id}>", mention.name)
      sentence = sentence.replace(f"<@!{mention.id}>", mention.name)  # Fallback

    text = f"``{get(f'http://artii.herokuapp.com/make?text={sentence}').text}``"

    if text == "````":
      return await ctx.send(embed = Tools.error("Your text contains unsupported characters."))

    try:
      return await ctx.send(text)

    except Exception:
      return await ctx.send(embed = Tools.error("Your text was too long to turn into ascii art."))

# Link to bot
def setup(bot):
  bot.add_cog(Ascii(bot))
