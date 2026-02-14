from discord import app_commands
from discord.ext import commands
import discord
import random
import string
import sys

sys.stdout.write("\x1b]2;Bot\x07")
sys.stdout.flush()

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(
    name="spam",
    description="Sends 5 messages in a row."
)
@app_commands.describe(text="text")
async def spam(interaction, text: str, randomize: bool = False, slowmode: bool = False, silent: bool = True):
    await interaction.response.send_message("peabox.org <3", ephemeral=True, silent=True)

    ws = interaction.followup

    if (len(text)>2000):
        # above message size limit
        print("message above limit")
        return

    if (randomize):
        available_length = 1999-len(text)

        if (available_length < 6):
            randomize = False
    
    subtext = text
    for i in range(0,5):
        if (randomize):
            x = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(6))
            subtext=text+" "+x
        await ws.send(subtext, silent=silent)
        if (slowmode):
            return

@tree.command(
    name="send",
    description="Sends a single message."
)
@app_commands.describe(text="send")
async def send(interaction, text: str, silent: bool = True):
    await interaction.response.send_message("peabox.org <3", ephemeral=True, silent=True)

    ws = interaction.followup
    await ws.send(text, silent=silent)

@client.event
async def on_ready():
    print("Syncing Tree...")
    await tree.sync()
    print(f"Logged in as {client.user}!")
    print(f"Install bot at: https://discord.com/oauth2/authorize?client_id={client.application_id}")

try:
    client.run(sys.argv[1])#, log_handler=None)
except Exception as e:
    print(str(e))
input("Press `Enter` to continue.")
