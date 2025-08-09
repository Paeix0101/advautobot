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

    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        chat_type = message["chat"]["type"]
        text = message.get("text", "").strip()
        user_id = message["from"]["id"]

        if text.lower() == "/accept":
            # Only run in private groups
            if chat_type != "supergroup":
                send_message(chat_id, "⚠️ This command only works in private supergroups with 'Approve New Members' enabled.")
                return {"ok": True}, 200

            if is_admin(chat_id, user_id):
                approve_all_pending_requests(chat_id)
            else:
                send_message(chat_id, "⚠️ You must be an admin to use this command.")

    return {"ok": True}, 200

def is_admin(chat_id, user_id):
    resp = requests.get(f"{TELEGRAM_API}/getChatAdministrators", params={"chat_id": chat_id})
    print("👮 Admin check response:", resp.json())
    if resp.ok:
        admins = resp.json().get("result", [])
        return any(admin["user"]["id"] == user_id for admin in admins)
    return False

def approve_all_pending_requests(chat_id):
    resp = requests.get(f"{TELEGRAM_API}/getChatJoinRequests", params={"chat_id": chat_id})
    print("📥 getChatJoinRequests response:", resp.json())

    if not resp.ok:
        send_message(chat_id, "❌ Failed to fetch join requests.")
        return

    requests_list = resp.json().get("result", [])
    if not requests_list:
        send_message(chat_id, "ℹ️ No pending join requests found.")
        return

    send_message(chat_id, f"🔍 Found {len(requests_list)} pending requests. Approving...")

    for req in requests_list:
        user_id = req["user"]["id"]
        approve = requests.post(f"{TELEGRAM_API}/approveChatJoinRequest", json={
            "chat_id": chat_id,
            "user_id": user_id
        })
        print(f"✅ Approve response for {user_id}:", approve.json())

        if approve.ok and approve.json().get("ok"):
            print(f"✅ Approved {user_id}")
        else:
            print(f"❌ Failed to approve {user_id}")

    send_message(chat_id, "✅ All pending join requests have been processed.")

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
    app.run(host="0.0.0.0", port=10000)