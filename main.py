import os
import random
import threading
import asyncio
import discord
from discord.ext import commands
from flask import Flask

# --- STEP A: Web Server (Keeps Render Awake) ---
app = Flask(__name__)

@app.route("/")
def home():
    return "24/7 Discord Anchor is Online & Secure!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

server_thread = threading.Thread(target=run_web_server)
server_thread.daemon = True
server_thread.start()


# --- STEP B: Discord 24/7 Voice Bot Setup ---
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Lock to prevent race conditions during reconnects
reconnect_lock = asyncio.Lock()


async def ensure_voice_connection():
    """Cleanly connects to the voice channel if not already connected."""
    if reconnect_lock.locked():
        return  # Reconnect is already in progress, skip duplicate call

    async with reconnect_lock:
        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            print(f"Channel ID {CHANNEL_ID} not found!")
            return

        # Check if voice client exists and is actually connected
        for vc in bot.voice_clients:
            if vc.channel.id == CHANNEL_ID and vc.is_connected():
                return  # Connected cleanly

        print("Voice connection missing or stale. Attempting clean reconnect...")
        
        # Cleanup stale clients
        for vc in list(bot.voice_clients):
            try:
                await vc.disconnect(force=True)
            except Exception as e:
                print(f"Cleanup error: {e}")

        await asyncio.sleep(2)  # Give Discord 2 seconds to clear old session

        try:
            await channel.connect(reconnect=True, timeout=30.0)
            print(f"Successfully reconnected to voice channel: {channel.name}")
        except Exception as e:
            print(f"Voice connection attempt failed: {e}")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await ensure_voice_connection()


@bot.event
async def on_voice_state_update(member, before, after):
    """Triggers only if the BOT ITSELF is moved or completely dropped from VC."""
    if member.id != bot.user.id:
        return

    # If the bot was disconnected from VC or moved to another channel
    if after.channel is None or after.channel.id != CHANNEL_ID:
        print("Bot voice state changed. Waiting 5s before verifying connection...")
        await asyncio.sleep(5)  # Let built-in reconnect try first before intervening
        await ensure_voice_connection()


# --- STEP C: Commands ---

@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! 🏓 Latency: `{latency}ms`")

@bot.command(name="coin")
async def coin(ctx):
    result = random.choice(["Heads 🪙", "Tails 🪙"])
    await ctx.send(f"Flipped a coin: **{result}**!")

@bot.command(name="roll")
async def roll(ctx):
    number = random.randint(1, 6)
    await ctx.send(f"🎲 You rolled a **{number}**!")

@bot.command(name="anchor")
async def anchor(ctx):
    responses = [
        "⚓ **VC Anchor Status:** Holding down the voice channel 24/7!",
        "⚓ **VC Anchor Status:** Still here! The streak is safe.",
        "⚓ **VC Anchor Status:** I haven't slept in days, but this VC is SECURED.",
        "⚓ **VC Anchor Status:** Brick by brick, hour by hour. 1,000 hours here we come!",
        "⚓ **VC Anchor Status:** Standing guard so you don't lose your streak!",
        "⚓ **VC Anchor Status:** Rooted in this VC like an oak tree. We aren't moving."
    ]
    await ctx.send(random.choice(responses))


bot.run(TOKEN)
