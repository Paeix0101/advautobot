import os
import requests
from flask import Flask, request
from config import BOT_TOKEN, WEBHOOK_SECRET

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

def is_admin(chat_id, user_id):
    """Check if a user is admin in the chat."""
    resp = requests.get(f"{TELEGRAM_API}/getChatAdministrators", params={"chat_id": chat_id})
    if resp.ok:
        admins = resp.json().get("result", [])
        return any(admin["user"]["id"] == user_id for admin in admins)
    return False

def approve_all_join_requests(chat_id):
    """Approve all pending join requests for the given chat."""
    resp = requests.get(f"{TELEGRAM_API}/getChatJoinRequests", params={"chat_id": chat_id})
    if resp.ok:
        join_requests = resp.json().get("result", [])
        count = 0
        for req_data in join_requests:
            user_id = req_data["user"]["id"]
            approve_resp = requests.post(f"{TELEGRAM_API}/approveChatJoinRequest",
                                         json={"chat_id": chat_id, "user_id": user_id})
            if approve_resp.ok:
                count += 1
        return count
    return 0

@app.route(f"/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    update = request.get_json()
    print("Received update:", update)

    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()
        user_id = message["from"]["id"]

        if text.lower() == "/accept":
            if is_admin(chat_id, user_id):
                count = approve_all_join_requests(chat_id)
                requests.post(f"{TELEGRAM_API}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": f"✅ Approved {count} pending join requests."
                })
            else:
                requests.post(f"{TELEGRAM_API}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": "⚠️ Only admins can use this command."
                })

    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

