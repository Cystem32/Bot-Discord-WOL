# bot.py

import discord
from discord.ext import commands
from config import BOT_PREFIX, GUILD_ID, TOKEN, ROLE_ID, OWNER_ID

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    guild = bot.get_guild(GUILD_ID)
    print(f'Serveur : {guild.name}')
    activity = discord.Activity(type=discord.ActivityType.playing, name='By Cystem32')
    await bot.change_presence(activity=activity)
    print('By Cystem32')

@bot.event
async def on_member_update(before, after):
    if after.guild.id == GUILD_ID:
        if ROLE_ID in [role.id for role in after.roles]:
            print(f'{after.display_name} a obtenu le rôle {ROLE_ID}')

async def setup_hook():
    await bot.load_extension("commands")

bot.setup_hook = setup_hook

bot.run(TOKEN)
