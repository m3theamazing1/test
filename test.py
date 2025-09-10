import discord
from discord.ext import commands
import json
import os
from discord.utils import get


intents = discord.Intents.default()
intents.message_content = True
last_author = {}  # channel_id : user_id

bot = commands.Bot(command_prefix="!", intents=intents)

COUNT_FILE = "counts.json"
LOG_FILE = "message_log.json"
ALLOWED_CHANNELS = [1414853107539644498, 1415179132341456896]

def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return []

def save_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f)

message_log = load_log()
Max_Log_Length = 1000
if len(message_log) > Max_Log_Length:
    message_log = message_log[-Max_Log_Length:] 
    save_log(message_log)


def load_counts():
    if os.path.exists(COUNT_FILE):
        with open(COUNT_FILE, "r") as f:
            return json.load(f)
    return {}

def save_counts(data):
    with open(COUNT_FILE, "w") as f:
        json.dump(data, f)

counts = load_counts()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    print("Loaded counts:", counts)
    
@bot.command()
async def purge(ctx):
    print("it's purgin' time")
    await ctx.send("it's over", delete_after=3)
    deleted = 0
    async for message in ctx.channel.history(limit = 10000):
        try:
            await message.delete()
            deleted += 1
        except (discord.Forbidden, discord.NotFound):
            pass
    await ctx.send(f"purge complete: {deleted} messages deleted", delete_after=10)


@bot.command()
async def send(ctx, *, content: str = None):

    role = get(ctx.author.roles, name="Heaven")

    if not role:
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass
        await ctx.send("❌ You don't have permission to use this command.", delete_after=3)
        return

    if not content:
        await ctx.send("⚠️ You must provide a message after the command.", delete_after=3)
        return

    # Try to delete the command message, ignore if not found
    try:
        await ctx.message.delete()
    except (discord.Forbidden, discord.NotFound):
        pass

    await ctx.send(f"{content}")

@bot.command()
async def reset(ctx):
    if ctx.channel.id not in ALLOWED_CHANNELS:
        return
    role = get(ctx.author.roles, name="Heaven")
    if not role:
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass
        await ctx.send("YOU of all people can't reset the count, dumbass", delete_after=3)
        return
    global counts, last_author
    channel_id = str(ctx.channel.id)
    counts[channel_id] = 0
    save_counts(counts)
    await ctx.send("Count has been reset to 0")
    print(f"[{ctx.channel.name}] Count reset to 0 by {ctx.author}")
    channel_id = str(ctx.channel.id)
    last_author[channel_id] = None  

@bot.event
async def on_message(message):
    global counts, message_log
    if message.author == bot.user:
        return
    
    if message.channel.id not in ALLOWED_CHANNELS:
        return

    if message.content.startswith(("!send", "!reset", "!purge")):
        await bot.process_commands(message)
        return
    
    channel_id = str(message.channel.id)

    # Log the message
    message_data = {
        "message_id": message.id,
        "channel_id": message.channel.id,
        "author_id": message.author.id,
        "content": message.content,
        "timestamp": str(message.created_at),
        "message_id": message.id
    }
    message_log.append(message_data)
    save_log(message_log)

    # Ensure channel initialized
    if channel_id not in last_author:
        last_author[channel_id] = None
    if channel_id not in counts:
        counts[channel_id] = 0

    # Counting logic
    should_delete = False
    reason = None

    if message.content.isdigit():
        number = int(message.content)

        if last_author[channel_id] == message.author.id:
            should_delete = True
            reason = f"{message.author.mention}, you can't count by yourself, dumbass"
        elif number == counts[channel_id] + 1:
            counts[channel_id] += 1
            save_counts(counts)
            print(f"[{message.channel.name}] Count is now {counts[channel_id]}")
            last_author[channel_id] = message.author.id

        else:
            should_delete = True
            reason = f"{message.author.mention}, wrong number, dumbass"
    else:
        should_delete = True
        reason = f"{message.author.mention}, this is a counting channel, dumbass"

    if should_delete:
        try:
            await message.delete()
            await message.channel.send(reason, delete_after=3)

            message_log = [m for m in message_log if m.get("message_id") != message.id]
            save_log(message_log)

        except (discord.Forbidden, discord.NotFound):
            print("Failed to delete message. Leaving it in log for retry.")
            pass
    
bot.run(os.environ.get('DISCORD_TOKEN'))
