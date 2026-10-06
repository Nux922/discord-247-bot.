import os
import random
import threading
import discord
from discord.ext import commands
from flask import Flask

# --- STEP A: Web Server (Keeps Render Awake) ---
app = Flask(__name__)

@app.route("/")
def home():
    return "24/7 Discord Anchor is Online & Secure!"

def run_web_server():
    # Render assigns its port via PORT environment variable (defaulting to 10000)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

server_thread = threading.Thread(target=run_web_server)
server_thread.daemon = True
server_thread.start()


# --- STEP B: Discord 24/7 Voice Bot Setup ---
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True  # Required for prefix commands

bot = commands.Bot(command_prefix="!", intents=intents)


async def ensure_voice_connection():
    """Cleanly connects to the voice channel if not already connected."""
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"Channel ID {CHANNEL_ID} not found!")
        return

    # Check if we are already connected to the target channel
    for vc in bot.voice_clients:
        if vc.channel.id == CHANNEL_ID and vc.is_connected():
            return  # Already connected cleanly, do nothing
        try:
            await vc.disconnect(force=True)
        except Exception as e:
            print(f"Cleanup error: {e}")

    try:
        await channel.connect(reconnect=True, timeout=30.0)
        print(f"Successfully connected to voice channel: {channel.name}")
    except Exception as e:
        print(f"Voice connection failed: {e}")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await ensure_voice_connection()


@bot.event
async def on_voice_state_update(member, before, after):
    """Only triggers when the BOT ITSELF is moved or disconnected by a user."""
    if member.id != bot.user.id:
        return

    # Case: Bot was disconnected or moved away from the target channel
    if after.channel is None or after.channel.id != CHANNEL_ID:
        print("Bot was disconnected or moved! Rejoining target channel...")
        await ensure_voice_connection()


# --- STEP C: Lightweight Commands ---

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
