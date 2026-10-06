import os
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


# --- STEP B: Discord 24/7 Voice Bot ---
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


async def ensure_voice_connection():
    """Helper function to cleanly connect or reconnect to the voice channel."""
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("Channel ID not found!")
        return

    # Clean up existing active voice clients first
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
        # Case 1: Bot was manually kicked/disconnected from VC
        if after.channel is None:
            print("Bot was disconnected! Rejoining target channel...")
            await ensure_voice_connection()

        # Case 2: Bot was dragged/moved to a different channel
        elif after.channel.id != CHANNEL_ID:
            print("Bot was moved! Returning to target channel...")
            await ensure_voice_connection()


bot.run(TOKEN)
