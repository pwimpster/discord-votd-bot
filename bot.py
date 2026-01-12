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
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
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

@app.route("/healthz")
def healthz():
    return "ok", 200

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
# SEND VERSE (shared logic)
# -----------------------------
async def send_verse(channel):
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

# -----------------------------
# SCHEDULED TASK (8:00 AM CT)
# -----------------------------
@tasks.loop(minutes=1)
async def send_votd():
    global last_sent_date

    now = datetime.now(CENTRAL_TZ)
    print(f"⏰ VOTD check: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    if now.hour != 8 or now.minute != 0:
        return

    if last_sent_date == now.date():
        return

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ Channel not found")
        return

    await send_verse(channel)
    last_sent_date = now.date()
    print("✅ Daily VOTD sent")

# -----------------------------
# SLASH COMMAND: /votd now
# -----------------------------
@bot.tree.command(name="votd", description="Get the Verse of the Day now")
async def votd_now(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    channel = interaction.channel
    await send_verse(channel)

    await interaction.followup.send("📖 Verse of the Day sent!")

# -----------------------------
# BOT EVENTS
# -----------------------------
@bot.event
async def on_ready():
    print(f"[DISCORD] Logged in as {bot.user}")
    await bot.tree.sync()

    if not send_votd.is_running():
        send_votd.start()
        print("[VOTD] Scheduler started")

# -----------------------------
# START EVERYTHING
# -----------------------------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(DISCORD_TOKEN)
