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

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        try:
            await channel.connect(reconnect=True)
            print(f"Connected to target voice channel: {channel.name}")
        except Exception as e:
            print(f"Connection failed: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    """
    SECURITY & RECONNECT GUARDRAILS:
    1. If disconnected, rejoin target channel automatically.
    2. If moved to another channel, return to target channel automatically.
    """
    if member.id == bot.user.id:
        # Case 1: Bot was kicked/disconnected from VC
        if after.channel is None:
            print("Bot was disconnected! Rejoining target channel...")
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                try:
                    await channel.connect(reconnect=True)
                except Exception as e:
                    print(f"Failed to rejoin: {e}")
        
        # Case 2: Someone moved the bot to another voice channel
        elif after.channel.id != CHANNEL_ID:
            print("Bot was moved to another channel! Returning to target channel...")
            target_channel = bot.get_channel(CHANNEL_ID)
            if target_channel:
                for vc in bot.voice_clients:
                    await vc.disconnect()
                await target_channel.connect(reconnect=True)

bot.run(TOKEN)
