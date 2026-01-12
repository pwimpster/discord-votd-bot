import os
import discord
from discord.ext import commands, tasks
import aiohttp
from datetime import datetime
import pytz
from flask import Flask
import threading

# -----------------------------
# CONFIG (CHANGE THESE)
# -----------------------------
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # REQUIRED ENV VAR
VOTD_API_URL = "https://bible-votd-api.onrender.com/votd_json"

CENTRAL_TZ = pytz.timezone("US/Central")
last_sent_date = None

# -----------------------------
# DISCORD BOT SETUP
# -----------------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------
# FLASK KEEP-ALIVE (Render)
# -----------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Discord VOTD Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# -----------------------------
# FETCH JSON VOTD
# -----------------------------
async def fetch_votd_json():
    async with aiohttp.ClientSession() as session:
        async with session.get(VOTD_API_URL, timeout=10) as resp:
            if resp.status != 200:
                raise ValueError("Failed to fetch VOTD")
            return await resp.json()

# -----------------------------
# SLASH COMMAND: /votd
# -----------------------------
@bot.tree.command(name="votd", description="Get today's Verse of the Day")
async def votd(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        data = await fetch_votd_json()

        message = (
            f"📖 **Verse of the Day**\n\n"
            f"“{data['text']}”\n"
            f"— *{data['reference']}*\n\n"
            f"• PwimpMyWide"
        )

        await interaction.followup.send(message)

    except Exception as e:
        print("❌ /votd error:", e)
        await interaction.followup.send(
            "⚠️ Something went wrong fetching the Verse of the Day.",
            ephemeral=True
        )

# -----------------------------
# DAILY SCHEDULED POST (8 AM CT)
# -----------------------------
@tasks.loop(minutes=1)
async def send_votd():
    global last_sent_date

    now = datetime.now(CENTRAL_TZ)

    if now.hour != 8 or now.minute != 0:
        return

    if last_sent_date == now.date():
        return

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ Channel not found")
        return

    try:
        data = await fetch_votd_json()

        message = (
            f"📖 **Verse of the Day**\n\n"
            f"“{data['text']}”\n"
            f"— *{data['reference']}*\n\n"
            f"• PwimpMyWide"
        )

        await channel.send(message)
        last_sent_date = now.date()
        print("✅ Scheduled VOTD sent")

    except Exception as e:
        print("❌ Scheduled VOTD error:", e)

# -----------------------------
# BOT READY
# -----------------------------
@bot.event
async def on_ready():
    print(f"[DISCORD] Logged in as {bot.user}")
    await bot.tree.sync()

    if not send_votd.is_running():
        send_votd.start()

# -----------------------------
# START EVERYTHING
# -----------------------------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(DISCORD_TOKEN)
