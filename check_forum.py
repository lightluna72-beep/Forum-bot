def main():
    payload = {
        "content": "GitHub Actions 定期実行テスト"
    }
    discord_post(f"/channels/{NOTIFY_CHANNEL_ID}/messages", payload)
    print("done")
    
    print("checker started")
print("guild:", GUILD_ID)
print("forum:", FORUM_CHANNEL_ID)
print("notify:", NOTIFY_CHANNEL_ID)

    initialized = state.get("initialized", False)
    seen = set(str(x) for x in state.get("seen_message_ids", []))
    new_seen = list(state.get("seen_message_ids", []))

    threads = fetch_active_forum_threads()
    threads = sorted(threads, key=lambda t: int(t["id"]))

    for thread in threads:
        messages = fetch_recent_messages(thread["id"], limit=10)
        messages = list(reversed(messages))

        for idx, msg in enumerate(messages):
            msg_id = str(msg["id"])

            if msg_id in seen:
                continue

            if msg.get("author", {}).get("bot"):
                new_seen.append(msg_id)
                seen.add(msg_id)
                continue

            # 初回だけ通知せず登録だけする
            if not initialized:
                new_seen.append(msg_id)
                seen.add(msg_id)
                continue

            kind = "新規投稿" if idx == 0 else "返信"
            notify_message(msg, thread["name"], kind)

            new_seen.append(msg_id)
            seen.add(msg_id)

    state["initialized"] = True
    state["seen_message_ids"] = new_seen
    save_state(state)
    print("done")