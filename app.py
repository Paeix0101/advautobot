from flask import Flask, request
import requests
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8377271454:AAGZb39SXDRYfVBY2Zz-JXe8FfYXeCyYX8M")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "x8d72n9kqp92s")  # Your webhook secret

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot is running", 200

@app.route(f"/webhook/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    data = request.get_json()
    print("🔔 Incoming update:", data)

    # Check for /accept command
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()
        from_user = message["from"]

        if text.lower() == "/accept":
            if is_admin(chat_id, from_user["id"]):
                count = approve_all_pending_requests(chat_id)
                send_message(chat_id, f"✅ Approved {count} pending requests.")
            else:
                send_message(chat_id, "⚠️ Only admins can use this command.")

    return {"ok": True}, 200

def is_admin(chat_id, user_id):
    """Check if user is admin"""
    resp = requests.get(f"{TELEGRAM_API}/getChatAdministrators", params={"chat_id": chat_id})
    if resp.ok:
        admins = resp.json().get("result", [])
        return any(admin["user"]["id"] == user_id for admin in admins)
    return False

def approve_all_pending_requests(chat_id):
    """Approve all pending join requests"""
    resp = requests.get(f"{TELEGRAM_API}/getChatJoinRequests", params={"chat_id": chat_id})
    if resp.ok:
        requests_list = resp.json().get("result", [])
        count = 0
        for req in requests_list:
            user_id = req["from"]["id"]
            approve = requests.post(f"{TELEGRAM_API}/approveChatJoinRequest", params={
                "chat_id": chat_id,
                "user_id": user_id
            })
            if approve.ok:
                count += 1
                print(f"✅ Approved user {user_id}")
            else:
                print(f"❌ Failed to approve {user_id}: {approve.text}")
        return count
    else:
        print(f"❌ Failed to get join requests: {resp.text}")
        return 0

def send_message(chat_id, text):
    """Send a message to the chat"""
    requests.post(f"{TELEGRAM_API}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

@app.route("/set-webhook")
def set_webhook():
    """Set the bot webhook"""
    webhook_url = f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/webhook/{WEBHOOK_SECRET}"
    resp = requests.get(f"{TELEGRAM_API}/setWebhook", params={"url": webhook_url})
    return resp.json()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)