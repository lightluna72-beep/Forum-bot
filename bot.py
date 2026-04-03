import os
import discord

TOKEN = os.getenv("BOT_TOKEN")

FORUM_CHANNEL_ID = int(os.getenv("FORUM_CHANNEL_ID"))
NOTIFY_CHANNEL_ID = int(os.getenv("NOTIFY_CHANNEL_ID"))

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"起動: {client.user}")

@client.event
async def on_thread_create(thread):
    if thread.parent_id != FORUM_CHANNEL_ID:
        return

    channel = client.get_channel(NOTIFY_CHANNEL_ID)

    embed = discord.Embed(
        title="フォーラム更新",
        description=thread.name,
        url=thread.jump_url
    )

    await channel.send(embed=embed)

client.run(TOKEN)