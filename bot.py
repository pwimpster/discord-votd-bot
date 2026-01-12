import os
import discord
from discord.ext import commands
import aiohttp
from flask import Flask
import threading

# -----------------------------
# CONFIG (CHANGE THESE)
# -----------------------------
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
VOTD_API_URL = "https://bible-votd-api.onrender.com/votd_json"

# -----------------------------
# DISCORD BOT
# -----------------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------
# FLASK KEEP-ALIVE
# -----------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Discord VOTD Image Bot running"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# -----------------------------
# FETCH JSON
# -----------------------------
async def fetch_votd_json():
    async with aiohttp.ClientSession() as session:
        async with session.get(VOTD_API_URL, timeout=10) as resp:
            return await resp.json()

# -----------------------------
# SLASH COMMAND: /votd image
# -----------------------------
@bot.tree.command(name="votd_image", description="Verse of the Day with image")
async def votd_image(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        data = await fetch_votd_json()

        embed = discord.Embed(
            title="📖 Verse of the Day",
            description=f"“{data['text']}”\n\n— *{data['reference']}*",
            color=0x6A5ACD
        )

        embed.set_image(url=data["image_url"])
        embed.set_footer(text="PwimpMyWide")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        print("❌ /votd_image error:", e)
        await interaction.followup.send(
            "⚠️ Failed to load Verse of the Day image.",
            ephemeral=True
        )

# -----------------------------
# READY
# -----------------------------
@bot.event
async def on_ready():
    print(f"[DISCORD] Logged in as {bot.user}")
    await bot.tree.sync()

# -----------------------------
# START
# -----------------------------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(DISCORD_TOKEN)
