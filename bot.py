import os
import discord
import aiohttp
from discord.ext import commands, ipc
import asyncpg
import logging
from collections import Counter
import time
import datetime
import os
import discord


intents=discord.Intents.default()
client = commands.AutoShardedBot(command_prefix=["ami ", "Ami ", "a!"], intents=intents)
start_time = datetime.datetime.utcnow()

os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
client.load_extension('jishaku')

for filename in os.listdir('./cogs'):
  if filename.endswith('.py'):
    client.load_extension(f'cogs.{filename[:-3]}')
    
  else:
    print(f'Unable to load {filename[:-3]}')

async def create_db_pool():
    client.pg_con = await asyncpg.create_pool(database="postgres", user="postgres", password="postgres")


client.session = aiohttp.ClientSession()
client.socket_receive = 0
client.socket_stats = Counter()
client.start_time = time.time()

client.codes = {
      1: "HEARTBEAT",
      2: "IDENTIFY",
      3: "PRESENCE",
      4: "VOICE_STATE",
      5: "VOICE_PING",
      6: "RESUME",
      7: "RECONNECT",
      8: "REQUEST_MEMBERS",
      9: "INVALIDATE_SESSION",
      10: "HELLO",
      11: "HEARTBEAT_ACK",
      12: "GUILD_SYNC"
  }

logging.getLogger('asyncio').setLevel(logging.CRITICAL)

@client.event
async def on_ready():
    print(f"Name : {client.user.name}\nID : {client.user.id}\nLoading all cogs...")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=f"amidiscord.xyz"))



@client.command(help="See the ami uptime from the last reboot", pass_context=True)
async def uptime(ctx: commands.Context):
    now = datetime.datetime.utcnow()
    delta = now - start_time
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    if days:
        time_format = "**{d}** days, **{h}** hours, **{m}** minutes, and **{s}** seconds."
    else:
        time_format = "**{h}** hours, **{m}** minutes, and **{s}** seconds."
    uptime_stamp = time_format.format(d=days, h=hours, m=minutes, s=seconds)
    em = discord.Embed(description="From the last restart, i've been online for:\n{}".format(uptime_stamp), color=0xffcff1)
    await ctx.send(embed=em)


client.loop.run_until_complete(create_db_pool())
token="Ami Token Omitted"
client.run(token)
