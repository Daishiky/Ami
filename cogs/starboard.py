import discord
from discord.ext import commands
import datetime
import random
import typing
import asyncio
import weakref
from util.defs import is_team

class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.locks = weakref.WeakValueDictionary()

    def star_emoji(self, stars):
        if 5 > stars >= 0:
            return '⭐'
        elif 10 > stars >= 5:
            return '🌟'
        elif 25 > stars >= 10:
            return '✨'
        else:
            return '🎇'

    async def get_starboard(self, payload):
        data = await self.bot.db.fetch("SELECT * FROM starboards_settings WHERE guild_id = $1", payload.guild_id)
        if not data:
            return False

        return data

    async def update_starboard(self, guild, channel, message, count):
        if not guild:
            return False

        if not channel:
            return False
        
        channel = self.bot.get_channel(channel)

        content = message.content
        atch = None
        
        if message.attachments:
            atch = message.attachments[0].url
        
        embed = discord.Embed(
            description = content,
            color = self.bot.color,
            timestamp = datetime.datetime.utcnow()
        )
        embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)
        embed.add_field(name='Original Message', value=f"[Click here!]({message.jump_url})", inline=False)
        if atch:
            embed.set_image(url=atch)

        fmt = f"{self.star_emoji(count)} **{count}** {channel.mention} ~ {message.id}"

        lock = self.locks.get(guild.id)
        if lock is None:
            self.locks[guild.id] = lock = asyncio.Lock()

        async with lock:
            data = await self.bot.db.fetchrow('SELECT * FROM starboards WHERE message_id = $1', message.id)
            if not data:
                
                m = await channel.send(fmt, embed=embed)

                await self.bot.db.execute("""
                    INSERT INTO starboards (guild_id, channel_id, message_id, star_message_id, stars_count, author_id)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    guild.id,
                    channel.id,
                    message.id,
                    m.id,
                    count,
                    message.author.id
                )
            else:
                if data['stars_count'] >= count:
                    return

                c = discord.utils.get(self.bot.cached_messages, id=data['star_message_id'])
                if not c:
                    c = await channel.fetch_message(data['star_message_id'])
                await c.edit(content=fmt, embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Starboard loaded")

    @commands.group(help="Starboard commands, to manage the stardboard in the current guild", aliases=['star'])
    async def starboard(self, ctx):
        if not ctx.invoked_subcommand:
            data = await self.bot.db.fetch("SELECT * FROM starboards_settings WHERE guild_id = $1", ctx.guild.id)
            if not data:
                return await ctx.reply("❌ This guild has not a starboard channel.")

            ch = ctx.guild.get_channel(data[0]['channel_id'])
            if not ch:
                return await ctx.reply(f"❌ The starboard channel for this guild is unavailable")

            await ctx.reply(f"⭐ {ch.mention}")

    @starboard.command(help="Set the starboard channel for the guild. If already one is set, it'll be overriden by the new one.")
    async def set(self, ctx, channel: discord.TextChannel):
        await self.bot.db.execute("INSERT INTO starboards_settings (guild_id, channel_id) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET channel_id = $2", ctx.guild.id, channel.id)
        await ctx.reply(f"Alright, {channel.mention} has been set as starboard channel for this guild.")

    @starboard.command(help="Disable the starboard for the guild and deletes the starboard channel if permissions available.")
    async def delete(self, ctx):
        data = await self.bot.db.fetch("SELECT * FROM starboards_settings WHERE guild_id = $1", ctx.guild.id)
        if not data:
            return await ctx.reply("❌ This guild has not a starboard channel yet.")

        ch = ctx.guild.get_channel(data[0]['channel_id'])
        if not ch:
            return await ctx.reply(f"❌ Starboard channel {data[0]['channel_id']} not found in the guild.")

        await self.bot.db.fetch("DELETE FROM starboards WHERE star_channel_id = $1", ch.id)
        await self.bot.db.execute("DELETE FROM starboards_settings WHERE guild_id = $1", ctx.guild.id)

        if ctx.me.guild_permissions.manage_channels:
            await ch.delete()

        await ctx.reply("All the starboard settings for this guild has been deleted.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id != 800176902765674496:
            return

        if payload.channel_id != 880917439179792574:
            return

        chan = self.bot.get_channel(payload.channel_id)

        message = await chan.fetch_message(payload.message_id)
        if message.reactions[0].emoji == '⭐' and message.reactions[0].count >= 4:
            starboard = await self.get_starboard(payload)

            if starboard is False:
                return

            await self.update_starboard(
                self.bot.get_guild(payload.guild_id), 
                starboard[0]['channel_id'], 
                message, 
                message.reactions[0].count
            )

def setup(bot):
    bot.add_cog(Starboard(bot))




