import os
import discord

TOKEN = os.getenv("BOT_TOKEN")
FORUM_CHANNEL_ID = int(os.getenv("FORUM_CHANNEL_ID"))
NOTIFY_CHANNEL_ID = int(os.getenv("NOTIFY_CHANNEL_ID"))

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

def is_image_attachment(attachment: discord.Attachment) -> bool:
    if attachment.content_type and attachment.content_type.startswith("image/"):
        return True

    filename = attachment.filename.lower()
    image_exts = [".png", ".jpg", ".jpeg", ".gif", ".webp"]
    return any(filename.endswith(ext) for ext in image_exts)

def shorten(text: str, length: int = 300) -> str:
    if not text:
        return "本文なし"
    text = text.strip()
    if len(text) <= length:
        return text
    return text[:length] + "..."

async def send_forum_notification(
    *,
    title: str,
    author_name: str,
    content: str,
    jump_url: str,
    attachments,
):
    channel = client.get_channel(NOTIFY_CHANNEL_ID)
    if channel is None:
        return

    description = f"**投稿者:** {author_name}\n\n{shorten(content)}\n\n[元のメッセージを見る]({jump_url})"

    non_image_files = []
    image_url = None

    for attachment in attachments:
        if is_image_attachment(attachment) and image_url is None:
            image_url = attachment.url
        else:
            non_image_files.append(f"[{attachment.filename}]({attachment.url})")

    if non_image_files:
        description += "\n\n**添付ファイル:**\n" + "\n".join(non_image_files)

    embed = discord.Embed(
        title=title,
        description=description
    )

    if image_url:
        embed.set_image(url=image_url)

    await channel.send(embed=embed)

@client.event
async def on_ready():
    print(f"起動: {client.user}")

@client.event
async def on_thread_create(thread: discord.Thread):
    if thread.parent_id != FORUM_CHANNEL_ID:
        return

    try:
        starter_message = await thread.fetch_message(thread.id)
    except Exception:
        starter_message = None

    if starter_message:
        author_name = getattr(starter_message.author, "display_name", starter_message.author.name)
        content = starter_message.content or ""
        attachments = starter_message.attachments
        jump_url = starter_message.jump_url
    else:
        author_name = "不明"
        content = ""
        attachments = []
        jump_url = thread.jump_url

    await send_forum_notification(
        title=f"【新規投稿】{thread.name}",
        author_name=author_name,
        content=content,
        jump_url=jump_url,
        attachments=attachments,
    )

@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if not isinstance(message.channel, discord.Thread):
        return

    thread = message.channel

    if thread.parent_id != FORUM_CHANNEL_ID:
        return

    # スレッド作成時の最初の投稿そのものは on_thread_create で通知する想定
    if message.id == thread.id:
        return

    author_name = getattr(message.author, "display_name", message.author.name)

    await send_forum_notification(
        title=f"【返信】{thread.name}",
        author_name=author_name,
        content=message.content or "",
        jump_url=message.jump_url,
        attachments=message.attachments,
    )

client.run(TOKEN)