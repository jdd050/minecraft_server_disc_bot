import os
import discord

from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from typing import Final
from mcserver import MinecraftServer

global bot
global minecraft_server

# Bot start up stuff
load_dotenv()
token: Final[str] = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot = commands.Bot(command_prefix="?", intents=intents)
minecraft_server = MinecraftServer()

# Runs when bot is online    
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot is online")
    return
 
# Gets discord API ping
@bot.tree.command(name="ping")
@app_commands.checks.cooldown(1, 10) # 1 use every 10 seconds
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Discord API latency: {round(bot.latency * 1000)} ms")
    return

# Starts the minecraft server (if it isn't already running)
@bot.tree.command(name="start_server")
@app_commands.checks.cooldown(1, 300) # 1 use every 5 minutes
async def start_server(interaction: discord.Interaction):
    # Check if the server is running
    if minecraft_server.is_running():
        await interaction.response.send_message("The Minecraft server is already running!", ephemeral=True)
        return
    # Try to start the server
    try:
        res = minecraft_server.start_server()
    except res == False:
        await interaction.response.send_message("Server failed to start! Contact <@315896399424389120>")
        return
    else:
        await interaction.response.send_message("Server successfully started!")
    return

# Stops the minecraft server (if it is running)
@bot.tree.command(name="stop_server")
@app_commands.checks.cooldown(1, 300) # 1 Use every 5 minutes
async def stop_server(interaction: discord.Interaction):
    # Only allow certain users to run this command (me, gabe, caleb, nathan)
    if interaction.user.id in [315896399424389120, 655709052948709376, 957091602692718632, 280003100364898304]:
        if not minecraft_server.is_running():
            await interaction.response.send_message("The Minecraft server is not running", ephemeral=True)
            return
        # Try to stop the server
        try:
            res = minecraft_server.stop_server()
            await interaction.response.send_message(str(res), ephemeral=True)
            return
        except res == False:
            await interaction.response.send_message("Failed to stop the server! Contact <@315896399424389120>")
            return
    else:
        interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
    return

# Allows the user to run a teleport command in the minecraft server
@bot.tree.command(name="mctp")
@app_commands.describe(
    mcname="The username of the player to be teleported", 
    xcoord="The x coordinate to teleport to (optional)",
    ycoord="The y coordinate to teleport to (optional)",
    zcoord="The z coordinate to teleport to (optional)",
    target_name="Name of the player to teleport to (optional)"
    )
@app_commands.checks.cooldown(1, 30) # 1 use every 30 seconds
async def mctp(
    interaction: discord.Interaction, 
    mcname: str,
    target_name: str = None,
    xcoord: int = None,
    ycoord: int = None,
    zcoord: int = None, 
):
    target = False
    coords = False
    if minecraft_server.is_running():
        if not mcname:
            await interaction.response.send_message("No player name provided! Cannot teleport.", ephemeral=True)
            return
        elif (not xcoord or not ycoord or not zcoord) and (not target_name):
            await interaction.response.send_message("Invalid command! Please provide X Y Z coordinates or a target player!", ephemeral=True)
            return
        elif (xcoord != None and ycoord != None and zcoord != None) and (not target_name):
            coords = True
            coordinates = [xcoord, ycoord, zcoord]
        elif target_name:
            target = True
        
        try:
            if coords:
                mc_command = f"execute as {mcname} run teleport @s {coordinates[0]} {coordinates[1]} {coordinates[2]}"
            if target:
                mc_command = f"execute as {mcname} run teleport @s {target_name}"
            res = minecraft_server.send_command(mc_command)
            await interaction.response.send_message(str(res), ephemeral=True)
            return
        except Exception as e:
            await interaction.response.send_message("Unknown error occured", ephemeral=True)
            return
    else:
        await interaction.response.send_message("Server is not running!", ephemeral=True)
        return
    
# Error handlers
@ping.error
async def on_ping_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.CommandOnCooldown):
        await interaction.response.send_message(
            f"You're on cooldown! Try again in {error.retry_after:.2f} seconds.",
            ephemeral=True
        )

@start_server.error
async def on_start_server_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.CommandOnCooldown):
        await interaction.response.send_message(
            f"You're on cooldown! Try again in {error.retry_after:.2f} seconds.",
            ephemeral=True
        )

@stop_server.error
async def on_stop_server_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.CommandOnCooldown):
        await interaction.response.send_message(
            f"You're on cooldown! Try again in {error.retry_after:.2f} seconds.",
            ephemeral=True
        )

@mctp.error
async def on_mctp_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.CommandOnCooldown):
        await interaction.response.send_message(
            f"You're on cooldown! Try again in {error.retry_after:.2f} seconds.",
            ephemeral=True
        )

bot.run(token)