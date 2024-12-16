import os
import discord

from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv, set_key, unset_key
from typing import Final
from mcserver import MinecraftServer

global bot
global minecraft_server
global DOTENV_PATH

# Bot start up stuff
DOTENV_PATH = os.path.abspath("./.env")
load_dotenv(DOTENV_PATH)
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
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id, "ping")) # 1 use every 10 seconds
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Discord API latency: {round(bot.latency * 1000)} ms")
    return

# Registers discord id to minecraft name
@bot.tree.command(name="register")
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id, "register"))
@app_commands.describe(mcname="The username of the player")
async def register(interaction: discord.Interaction, mcname: str):
    try:
        set_key(DOTENV_PATH, str(interaction.user.id), mcname)
    except Exception as e:
        await interaction.response.send_message("Failed to register username to your discord ID", ephemeral=True)
        return
    else:
        await interaction.response.send_message(f"Successfully registered minecraft name {mcname} to {interaction.user.name} ({interaction.user.id})", ephemeral=True)
        return

# Check if discord id is registered to a minecraft name
@bot.tree.command(name="checkregister")
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id, "checkregister"))
async def checkregister(interaction: discord.Interaction):
    try:
        res = os.getenv(str(interaction.user.id))
    except res == None:
        await interaction.response.send_message("Discord ID is not registered to a minecraft name")
    else:
        await interaction.response.send_message(f"Entry found: {res}")

# Unregisters discord id to minecraft name
@bot.tree.command(name="unregister")
@app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id, "unregister"))
async def unregister(interaction: discord.Interaction):
    try:
        unset_key(DOTENV_PATH, str(interaction.user.id))
    except Exception as e:
        await interaction.response.send_message("Failed to unregister username/discord_id reference. Are you sure you had one?")
        return
    else:
        await interaction.response.send_message(f"Successfully unregistered entry for {interaction.user.name} ({interaction.user.id})", ephemeral=True)

# Starts the minecraft server (if it isn't already running)
@bot.tree.command(name="start_server")
@app_commands.checks.cooldown(1, 300, key=lambda i: (i.user.id, "start_server")) # 1 use every 5 minutes
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
@app_commands.checks.cooldown(1, 300, key=lambda i: (i.user.id, "start_stop")) # 1 Use every 5 minutes
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
@bot.tree.command(name="tp")
@app_commands.describe(
    xcoord="The x coordinate to teleport to (optional)",
    ycoord="The y coordinate to teleport to (optional)",
    zcoord="The z coordinate to teleport to (optional)",
    target_name="Name of the player to teleport to (optional)"
    )
@app_commands.checks.cooldown(1, 30, key=lambda i: (i.user.id, "tp")) # 1 use every 30 seconds
async def tp(
    interaction: discord.Interaction, 
    target_name: str = None,
    xcoord: int = None,
    ycoord: int = None,
    zcoord: int = None, 
):
    target = False
    coords = False
    if minecraft_server.is_running():
        if os.getenv(str(interaction.user.id)) == None:
            await interaction.response.send_message("Discord ID is not registered to a minecraft name! Cannot teleport. Please run /register", ephemeral=True)
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
                mc_command = f"execute as {os.getenv(str(interaction.user.id))} run teleport @s {coordinates[0]} {coordinates[1]} {coordinates[2]}"
            if target:
                mc_command = f"execute as {os.getenv(str(interaction.user.id))} run teleport @s {target_name}"
            res = minecraft_server.send_command(mc_command) # need to fix logging
            await interaction.response.send_message("Command sent", ephemeral=True)
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

@tp.error
async def on_tp_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.CommandOnCooldown):
        await interaction.response.send_message(
            f"You're on cooldown! Try again in {error.retry_after:.2f} seconds.",
            ephemeral=True
        )

bot.run(token)