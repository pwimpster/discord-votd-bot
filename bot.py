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
# FETCH VOTD FROM API
# -----------------------------
async def fetch_votd():
    async with aiohttp.ClientSession() as session:
        async with session.get(VOTD_API_URL, timeout=10) as resp:
            if resp.status != 200:
                raise ValueError("VOTD API error")
            return await resp.text()


# -----------------------------
# SEND VERSE (SAFE VERSION)
# -----------------------------
async def send_verse(channel):
    verse_text = await fetch_votd()

    message = (
        f"📖 **Verse of the Day**\n\n"
        f"{verse_text}\n\n"
        f"• PwimpMyWide"
    )

    await channel.send(message)

# -----------------------------
# DAILY SCHEDULED TASK
# -----------------------------
@tasks.loop(minutes=1)
async def send_votd_daily():
    global last_sent_date

    now = datetime.now(CENTRAL_TZ)
    print(f"⏰ VOTD check: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    if now.hour != 8 or now.minute != 0:
        return

    if last_sent_date == now.date():
        return

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ Channel not found — check CHANNEL_ID")
        return

    try:
        await send_verse(channel)
        last_sent_date = now.date()
        print("✅ Daily VOTD sent")
    except Exception as e:
        print(f"❌ Daily VOTD error: {e}")

# -----------------------------
# SLASH COMMAND: /votd
# -----------------------------
@bot.tree.command(name="votd", description="Get the Verse of the Day now")
async def votd_now(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    try:
        await send_verse(interaction.channel)

        await interaction.followup.send(
            "📖 Verse of the Day sent!",
            ephemeral=True
        )

    except Exception as e:
        print(f"❌ /votd error: {e}")

        await interaction.followup.send(
            "⚠️ Something went wrong fetching the Verse of the Day.",
            ephemeral=True
        )

# -----------------------------
# BOT EVENTS
# -----------------------------
@bot.event
async def on_ready():
    print(f"[DISCORD] Logged in as {bot.user} (ID: {bot.user.id})")

    await bot.tree.sync()
    print("[DISCORD] Slash commands synced")

    if not send_votd_daily.is_running():
        send_votd_daily.start()
        print("[VOTD] Daily scheduler started")

# -----------------------------
# START EVERYTHING
# -----------------------------
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(DISCORD_TOKEN)

