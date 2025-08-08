from flask import Flask, request
import requests
import os
from config import BOT_TOKEN, WEBHOOK_SECRET

app = Flask(__name__)
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

@app.route("/")
def home():
    return "✅ Bot is running", 200

@app.route(f"/webhook/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    data = request.get_json()
    print("🔔 Incoming update:", data)

    # If it's a message
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()

        # Only act on /accept command
        if text.lower() == "/accept":
            # Check if user is admin
            user_id = message["from"]["id"]
            if is_admin(chat_id, user_id):
                approve_all_pending_requests(chat_id)
                send_message(chat_id, "✅ All pending join requests have been approved.")
            else:
                send_message(chat_id, "⚠️ You must be an admin to use this command.")

    return {"ok": True}, 200

def is_admin(chat_id, user_id):
    """Check if user is admin in the group/channel"""
    resp = requests.get(f"{TELEGRAM_API}/getChatAdministrators", params={"chat_id": chat_id})
    if resp.ok:
        admins = resp.json().get("result", [])
        return any(admin["user"]["id"] == user_id for admin in admins)
    return False

def approve_all_pending_requests(chat_id):
    """Fetch and approve all pending join requests"""
    resp = requests.get(f"{TELEGRAM_API}/getChatJoinRequests", params={"chat_id": chat_id})
    if resp.ok:
        requests_list = resp.json().get("result", [])
        for req in requests_list:
            user_id = req["from"]["id"]  # FIXED
            approve = requests.post(f"{TELEGRAM_API}/approveChatJoinRequest", json={
                "chat_id": chat_id,
                "user_id": user_id
            })
            if approve.ok:
                print(f"✅ Approved {user_id}")
            else:
                print(f"❌ Failed to approve {user_id}: {approve.text}")

def send_message(chat_id, text):
    requests.post(f"{TELEGRAM_API}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

@app.route("/set-webhook")
def set_webhook():
    webhook_url = f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/webhook/{WEBHOOK_SECRET}"
    resp = requests.get(f"{TELEGRAM_API}/setWebhook", params={"url": webhook_url})
    return resp.json()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # FIXED
    app.run(host="0.0.0.0", port=port)