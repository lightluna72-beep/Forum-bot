import json
import os
from pathlib import Path
import requests

BASE_URL = "https://discord.com/api/v10"

BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
GUILD_ID = os.environ["DISCORD_GUILD_ID"]
FORUM_CHANNEL_ID = os.environ["DISCORD_FORUM_CHANNEL_ID"]
NOTIFY_CHANNEL_ID = os.environ["DISCORD_NOTIFY_CHANNEL_ID"]

STATE_PATH = Path("state.json")
MAX_TRACKED_IDS = 2000

HEADERS = {
    "Authorization": f"Bot {BOT_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "forum-poller/1.0"
}


def load_state():
    if not STATE_PATH.exists():
        return {"seen_message_ids": []}
    with STATE_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    ids = state.get("seen_message_ids", [])
    state["seen_message_ids"] = ids[-MAX_TRACKED_IDS:]
    with STATE_PATH.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def discord_get(path, params=None):
    url = f"{BASE_URL}{path}"
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def discord_post(path, payload):
    url = f"{BASE_URL}{path}"
    r = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def is_image_attachment(att):
    content_type = att.get("content_type") or ""
    filename = (att.get("filename") or "").lower()
    if content_type.startswith("image/"):
        return True
    return filename.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))


def shorten(text, limit=300):
    if not text:
        return "本文なし"
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def fetch_active_forum_threads():
    data = discord_get(f"/guilds/{GUILD_ID}/threads/active")
    threads = data.get("threads", [])
    return [t for t in threads if str(t.get("parent_id")) == str(FORUM_CHANNEL_ID)]


def fetch_recent_messages(thread_id, limit=10):
    return discord_get(f"/channels/{thread_id}/messages", params={"limit": limit})


def build_embed(message, thread_name, kind):
    author = message.get("author", {})
    attachments = message.get("attachments", [])
    content = message.get("content", "")
    jump_url = (
        f"https://discord.com/channels/"
        f"{GUILD_ID}/{message['channel_id']}/{message['id']}"
    )

    image_url = None
    other_files = []

    for att in attachments:
        if is_image_attachment(att) and image_url is None:
            image_url = att.get("url")
        else:
            filename = att.get("filename", "file")
            url = att.get("url")
            if url:
                other_files.append(f"[{filename}]({url})")

    description = (
        f"**投稿者:** {author.get('global_name') or author.get('username', '不明')}\n\n"
        f"{shorten(content)}\n\n"
        f"[元のメッセージを見る]({jump_url})"
    )

    if other_files:
        description += "\n\n**添付ファイル:**\n" + "\n".join(other_files)

    embed = {
        "title": f"{thread_name}",
        "description": description
    }

    if image_url:
        embed["image"] = {"url": image_url}

    return embed


def notify_message(message, thread_name, kind):
    payload = {
        "embeds": [build_embed(message, thread_name, kind)]
    }
    discord_post(f"/channels/{NOTIFY_CHANNEL_ID}/messages", payload)


def main():
    state = load_state()
    seen = set(str(x) for x in state.get("seen_message_ids", []))
    new_seen = list(state.get("seen_message_ids", []))

    threads = fetch_active_forum_threads()

    # 古い順に流したいので thread作成時刻っぽいid順に昇順
    threads = sorted(threads, key=lambda t: int(t["id"]))

    for thread in threads:
        messages = fetch_recent_messages(thread["id"], limit=10)
        # messages APIは通常 新しい順なので逆順にして古い→新しいで通知
        messages = list(reversed(messages))

        for idx, msg in enumerate(messages):
            msg_id = str(msg["id"])
            if msg_id in seen:
                continue

            # bot自身の通知や他botはスキップ
            if msg.get("author", {}).get("bot"):
                new_seen.append(msg_id)
                seen.add(msg_id)
                continue

            kind = "新規投稿" if idx == 0 else "返信"
            notify_message(msg, thread["name"], kind)

            new_seen.append(msg_id)
            seen.add(msg_id)

    state["seen_message_ids"] = new_seen
    save_state(state)
    print("done")


if __name__ == "__main__":
    main()
