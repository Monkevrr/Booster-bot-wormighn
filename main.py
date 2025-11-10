import discord
from discord import app_commands
from discord.ext import commands
import os
import aiohttp
import webserver

DISCORD_TOKEN = os.environ['discordkey']
PLAYFAB_TITLE_ID = '4C42F'
PLAYFAB_SECRET_KEY = 'BO51N5M7O7MEEGOUOAK8BZEBO9K7F4WOKRTECE9M56OACZAXI9'
ALLOWED_SERVER_ID = 1319882768989163532
ALLOWED_CHANNEL_ID = 1374731642094227488

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

async def grant_playfab_item(playfab_id: str, item_id: str):
    """Grant an item to a PlayFab player"""
    url = f"https://{PLAYFAB_TITLE_ID}.playfabapi.com/Server/GrantItemsToUser"
    
    headers = {
        "Content-Type": "application/json",
        "X-SecretKey": PLAYFAB_SECRET_KEY
    }
    
    payload = {
        "PlayFabId": playfab_id,
        "ItemIds": [item_id],
        "Annotation": "Granted via Discord bot - Server Booster reward"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            result = await response.json()
            return result

def is_correct_server_and_channel():
    """Check if command is used in the correct server and channel"""
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.guild and interaction.guild.id == ALLOWED_SERVER_ID and interaction.channel_id == ALLOWED_CHANNEL_ID:
            return True
        return False
    return app_commands.check(predicate)

def has_server_booster_role():
    """Check if user has Server Booster role"""
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.guild:
            for role in interaction.user.roles:
                if role.name == "Server Booster":
                    return True
        return False
    return app_commands.check(predicate)

@bot.event
async def on_ready():
    print(f'{bot.user} is now online!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="iboosted", description="Claim your Boobundle cosmetic for boosting the server!")
@app_commands.describe(playfab_id="Your PlayFab ID")
@is_correct_server_and_channel()
@has_server_booster_role()
async def iboosted(interaction: discord.Interaction, playfab_id: str):
    """Grant Boobundle cosmetic to Server Boosters"""
    
    await interaction.response.defer(ephemeral=True)
    
    result = await grant_playfab_item(playfab_id, "Boobundle")
    
    if result.get("status") == "OK":
        await interaction.followup.send(
            f"✅ Successfully granted **Boobundle** cosmetic to PlayFab ID: `{playfab_id}`\n"
            f"Thank you for boosting the server! 🎉",
            ephemeral=True
        )
    else:
        error = result.get("errorMessage", "Unknown error")
        await interaction.followup.send(
            f"❌ Error granting cosmetic: {error}\n"
            f"Make sure your PlayFab ID is correct!",
            ephemeral=True
        )

@iboosted.error
async def iboosted_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        # Check which check failed
        if not interaction.guild or interaction.guild.id != ALLOWED_SERVER_ID or interaction.channel_id != ALLOWED_CHANNEL_ID:
            await interaction.response.send_message(
                "❌ ur a bad boy",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ You need the **Server Booster** role to use this command!",
                ephemeral=True
            )

webserver.keep_alive()
bot.run(DISCORD_TOKEN)
