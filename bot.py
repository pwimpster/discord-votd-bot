import os
import discord
from discord.ext import commands, tasks
import aiohttp
from datetime import datetime
import pytz
from flask import Flask
import threading

# -----------------------------
# CONFIG
# -----------------------------
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Discord channel ID
VOTD_API_URL = "https://bible-votd-api.onrender.com/votd"

CENTRAL_TZ = pytz.timezone("US/Central")
last_sent_date = None

# -----------------------------
# DISCORD BOT SETUP
# -----------------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------
# FLASK (keeps Render alive)
# -----------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Discord VOTD Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# -----------------------------
# FETCH VOTD
# -----------------------------
async def fetch_votd():
    async with aiohttp.ClientSession() as session:
        async with session.get(VOTD_API_URL) as resp:
            return await resp.json()

# -----------------------------
# SCHEDULED TASK
# -----------------------------
@tasks.loop(minutes=1)
async def send_votd():
    global last_sent_date

    now = datetime.now(CENTRAL_TZ)
    print(f"⏰ VOTD check: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # Only send at exactly 8:00 AM CT
    if now.hour != 8 or now.minute != 0:
        return

    # Prevent duplicate sends
    if last_sent_date == now.date():
        print("⚠️ VOTD already sent today")
        return

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ Channel not found — check CHANNEL_ID")
        return

    data = await fetch_votd()

    verse_text = data["text"]
    reference = data["reference"]
    image_url = data["image_url"]

    message = (
        f"📖 **Verse of the Day**\n\n"
        f"“{verse_text}”\n"
        f"— *{reference}*\n\n"
        f"[pic]({image_url}) • PwimpMyWide"
    )

    await channel.send(message)
    last_sent_date = now.date()

    print("✅ VOTD sent successfully")

# -----------------------------
# BOT EVENTS
# -----------------------------
@bot.event
async def on_ready():
    print(f"[DISCORD] Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"[DISCORD] Target channel ID: {CHANNEL_ID}")

    if not send_votd.is_running():
        send_votd.start()
        print("[VOTD] Scheduler started")
    else:
        print("[VOTD] Scheduler already running")

# -----------------------------
# START EVERYTHING
# -----------------------------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(DISCORD_TOKEN)
