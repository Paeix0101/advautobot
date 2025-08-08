import os
import requests
from flask import Flask, request

# Replace with your bot token
BOT_TOKEN = "8377271454:AAGZb39SXDRYfVBY2Zz-JXe8FfYXeCyYX8M"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

# Webhook endpoint (must match your Render webhook path)
WEBHOOK_PATH = "/x8d72n9kqp92s"

def approve_all_join_requests(chat_id):
    """Approve all pending join requests for the given chat."""
    url = f"{TELEGRAM_API}/getChatJoinRequests"
    params = {"chat_id": chat_id}
    resp = requests.get(url, params=params).json()

    if not resp.get("ok"):
        print("Failed to get join requests:", resp)
        return

    requests_list = resp.get("result", [])
    for req_data in requests_list:
        user_id = req_data["user"]["id"]
        approve_url = f"{TELEGRAM_API}/approveChatJoinRequest"
        approve_params = {"chat_id": chat_id, "user_id": user_id}
        approve_resp = requests.post(approve_url, data=approve_params).json()
        print(f"Approved {user_id}: {approve_resp}")

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = request.get_json()
    print("Received update:", update)

    # If message exists and is a command
    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        # Only trigger on /accept
        if text.strip() == "/accept":
            approve_all_join_requests(chat_id)
            requests.post(f"{TELEGRAM_API}/sendMessage", data={
                "chat_id": chat_id,
                "text": "✅ All pending join requests have been approved."
            })

    return "ok", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

