import os

# Bot token will come from Render's environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Random webhook secret
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "x8d72n9kqp92s")