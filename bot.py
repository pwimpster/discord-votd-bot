import os
import discord
from discord.ext import tasks, commands
from datetime import datetime, time, timedelta, timezone

# --- CONFIGURATION ---

# Timezone for America/Chicago (CST/CDT).
CT = timezone(timedelta(hours=-6))

# Read your bot token and channel ID from environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID_STR = os.getenv("DISCORD_CHANNEL_ID", "0")

try:
    CHANNEL_ID = int(CHANNEL_ID_STR)
except ValueError:
    CHANNEL_ID = 0

VERSE_OF_THE_DAY_URL = "https://www.bible.com/verse-of-the-day"

# --- DISCORD BOT SETUP ---

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

last_sent_date = None  # track if we've already sent today's verse


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"📡 Sending Verse of the Day to channel ID: {CHANNEL_ID}")
    send_votd.start()


@tasks.loop(minutes=1)
async def send_votd():
    """
    Check once a minute:
    - If it's 8:00 AM in America/Chicago
    - If we haven't already sent it today
    Then send the Verse of the Day link.
    """
    global last_sent_date

    if CHANNEL_ID == 0:
        print("⚠️ No valid DISCORD_CHANNEL_ID set. Skipping send.")
        return

    now = datetime.now(CT)
    today = now.date()

    if last_sent_date == today:
        return

    target = time(hour=8, minute=0, tzinfo=CT)

    if now.time().hour == target.hour and now.time().minute == target.minute:
        channel = bot.get_channel(CHANNEL_ID)
        if channel is None:
            print("⚠️ Channel not found. Double-check the channel ID.")
            return

        message = (
            "📖 **Verse of the Day**\n"
            f"Here’s today’s verse from the Bible App:\n{VERSE_OF_THE_DAY_URL}"
        )

        await channel.send(message)
        print(f"✅ Sent Verse of the Day for {today}")
        last_sent_date = today


@send_votd.before_loop
async def before_send_votd():
    await bot.wait_until_ready()


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN environment variable is not set.")
    if CHANNEL_ID == 0:
        raise RuntimeError(
            "DISCORD_CHANNEL_ID environment variable is missing or invalid."
        )
    bot.run(DISCORD_TOKEN)
