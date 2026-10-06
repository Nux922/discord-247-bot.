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
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

server_thread = threading.Thread(target=run_web_server)
server_thread.daemon = True
server_thread.start()


# --- STEP B: Discord 24/7 Voice Bot Setup ---
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True  # Required for prefix commands to read text messages

bot = commands.Bot(command_prefix="!", intents=intents)


async def ensure_voice_connection():
    """Helper function to cleanly connect or reconnect to the target voice channel."""
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("Channel ID not found! Check your CHANNEL_ID environment variable.")
        return

    # Clean up existing active voice clients first to prevent duplicate session errors
    for vc in bot.voice_clients:
        try:
            await vc.disconnect(force=True)
        except Exception as e:
            print(f"Error disconnecting existing client: {e}")

    try:
        await channel.connect(reconnect=True)
        print(f"Connected to voice channel: {channel.name}")
    except Exception as e:
        print(f"Connection failed: {e}")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await ensure_voice_connection()


@bot.event
async def on_voice_state_update(member, before, after):
    """
    AUTO-REJOIN GUARDRAILS:
    Triggers whenever ANY user or bot changes voice states in the server.
    """
    if member.id == bot.user.id:
        # Case 1: Bot was disconnected or moved away from the target channel
        if after.channel is None or after.channel.id != CHANNEL_ID:
            print("Bot disconnected or moved! Returning to target channel...")
            await ensure_voice_connection()


# --- STEP C: Lightweight Commands ---

@bot.command(name="ping")
async def ping(ctx):
    """Responds with the bot's current ping/latency."""
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! 🏓 Latency: `{latency}ms`")

@bot.command(name="coin")
async def coin(ctx):
    """Flips a coin."""
    result = random.choice(["Heads 🪙", "Tails 🪙"])
    await ctx.send(f"Flipped a coin: **{result}**!")

@bot.command(name="roll")
async def roll(ctx):
    """Rolls a 6-sided die."""
    number = random.randint(1, 6)
    await ctx.send(f"🎲 You rolled a **{number}**!")

@bot.command(name="anchor")
async def anchor(ctx):
    """Displays a random status line for the VC anchor."""
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
