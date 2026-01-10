import os
from threading import Thread
from datetime import datetime, time, timedelta, timezone

import discord
from discord.ext import tasks, commands
from flask import Flask

# ------------------------
# FLASK SERVER FOR RENDER
# ------------------------

server = Flask(__name__)

@server.route("/")
def home():
    return "Discord VOTD bot is running!"

def run_server():
    port = int(os.getenv("PORT", "10000"))  # Render sets PORT automatically
    print(f"[FLASK] Starting web server on port {port}")
    server.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.daemon = True
    t.start()

# ------------------------
# DISCORD BOT
# ------------------------

# Central Time (adjust if you want a different TZ)
CT = timezone(timedelta(hours=-6))

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID_STR = os.getenv("DISCORD_CHANNEL_ID", "0")

try:
    CHANNEL_ID = int(CHANNEL_ID_STR)
except ValueError:
    CHANNEL_ID = 0

VERSE_OF_THE_DAY_URL = "https://www.bible.com/verse-of-the-day"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

last_sent_date = None  # track if we've sent today's verse yet


@bot.event
async def on_ready():
    print(f"[DISCORD] Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"[DISCORD] Target channel ID: {CHANNEL_ID}")
    send_votd.start()


@tasks.loop(minutes=1)
async def send_votd():
    """Check once per minute and send at 8:00 AM CT if not sent yet."""
    global last_sent_date

    if CHANNEL_ID == 0:
        print("[WARN] DISCORD_CHANNEL_ID not set or invalid.")
        return

    now = datetime.now(CT)
    today = now.date()

    # Already sent today
    if last_sent_date == today:
        return

    target = time(hour=8, minute=0, tzinfo=CT)

    if now.time().hour == target.hour and now.time().minute == target.minute:
        channel = bot.get_channel(CHANNEL_ID)
        if channel is None:
            print("[WARN] Channel not found. Check DISCORD_CHANNEL_ID.")
            return

        msg = (
            "📖 **Verse of the Day**\n"
            f"Here’s today’s verse from the Bible App:\n{VERSE_OF_THE_DAY_URL}"
        )
        await channel.send(msg)
        last_sent_date = today
        print(f"[DISCORD] Sent VOTD for {today}")


@send_votd.before_loop
async def before_send_votd():
    await bot.wait_until_ready()


# Optional: command to trigger manually in Discord
@bot.command(name="votd")
async def votd_command(ctx: commands.Context):
    await ctx.send(
        f"📖 **Verse of the Day**\n{VERSE_OF_THE_DAY_URL}"
    )


# ------------------------
# START EVERYTHING
# ------------------------

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN environment variable is not set.")
    if CHANNEL_ID == 0:
        raise RuntimeError("DISCORD_CHANNEL_ID environment variable is missing or invalid.")

    # Start Flask keep-alive web server (for Render free Web Service)
    keep_alive()

    # Start Discord bot
    bot.run(DISCORD_TOKEN)


@tasks.loop(time=send_time)
async def send_daily_verse():
    print("📖 Verse of the Day task triggered")
    ...
