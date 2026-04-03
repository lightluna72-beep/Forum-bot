def main():
    state = load_state()
    seen = set(str(x) for x in state.get("seen_message_ids", []))
    new_seen = list(state.get("seen_message_ids", []))

    threads = fetch_active_forum_threads()
    threads = sorted(threads, key=lambda t: int(t["id"]))

    # 初回実行: 通知せず、既存メッセージを全部既読扱いにする
    first_run = len(seen) == 0

    for thread in threads:
        messages = fetch_recent_messages(thread["id"], limit=10)
        messages = list(reversed(messages))

        for idx, msg in enumerate(messages):
            msg_id = str(msg["id"])

            if msg_id in seen:
                continue

            # botメッセージはスキップ
            if msg.get("author", {}).get("bot"):
                new_seen.append(msg_id)
                seen.add(msg_id)
                continue

            if first_run:
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