# Zefoy Telegram Bot Configuration
# Supports Railway.app deployment

import os

# Telegram Bot Token
# Get from @BotFather on Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Admin Telegram IDs (for admin commands)
# Get from @userinfobot
admin_ids_str = os.getenv("ADMIN_IDS", "123456789")
ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]

# Bot Info
BOT_NAME = "ZefoyProBot"
BOT_USERNAME = "@ZefoyProBot"

# Service Settings
SERVICES = {
    "followers": {
        "name": "👥 Followers",
        "description": "Increase your TikTok followers",
        "min": 100,
        "max": 10000,
        "default": 1000,
        "cooldown": 3600,
        "icon": "👥"
    },
    "likes": {
        "name": "❤️ Likes",
        "description": "Get more likes on your videos",
        "min": 100,
        "max": 50000,
        "default": 1000,
        "cooldown": 1800,
        "icon": "❤️"
    },
    "views": {
        "name": "👀 Views",
        "description": "Boost your video views",
        "min": 1000,
        "max": 100000,
        "default": 5000,
        "cooldown": 900,
        "icon": "👀"
    },
    "shares": {
        "name": "📤 Shares",
        "description": "Increase video shares",
        "min": 100,
        "max": 10000,
        "default": 500,
        "cooldown": 3600,
        "icon": "📤"
    },
    "comments": {
        "name": "💬 Comments",
        "description": "Get custom comments on videos",
        "min": 10,
        "max": 1000,
        "default": 50,
        "cooldown": 7200,
        "icon": "💬"
    }
}

# File Paths
DATA_DIR = "data"
LOGS_DIR = "logs"
USERS_FILE = f"{DATA_DIR}/users.json"
ORDERS_FILE = f"{DATA_DIR}/orders.json"
COOLDOWNS_FILE = f"{DATA_DIR}/cooldowns.json"
STATS_FILE = f"{DATA_DIR}/stats.json"

# Messages
WELCOME_MESSAGE = """
🎉 *Welcome to Zefoy Pro Bot!* 🎉

🚀 *Get Free TikTok Engagement Instantly!*

✨ *What you can get:*
• 👥 Free Followers
• ❤️ Free Likes
• 👀 Free Views
• 📤 Free Shares
• 💬 Free Comments

⚡ *Features:*
✅ No login required
✅ Fast delivery
✅ 100% Safe
✅ Completely Free

🎯 *How to use:*
1️⃣ Select a service from menu
2️⃣ Enter your TikTok username/video link
3️⃣ Choose quantity
4️⃣ Get instant boost!

📌 *Note:* Please ensure your account is public!

👇 *Choose a service to start:*
"""

HELP_MESSAGE = """
❓ *How to use Zefoy Bot:*

*Step 1:* Select service (Followers/Likes/Views)
*Step 2:* Send your TikTok @username or video link
*Step 3:* Select quantity
*Step 4:* Wait for processing

⚠️ *Requirements:*
• Account must be PUBLIC
• Username format: @username (without @)
• Video link: Full TikTok URL

⏱️ *Cooldown Periods:*
• Views: 15 minutes
• Likes: 30 minutes
• Followers: 1 hour
• Shares: 1 hour
• Comments: 2 hours

🆘 *Support:* Use /help anytime
"""

# Auto-response messages
PROCESSING_MESSAGES = [
    "🔍 Validating your TikTok account...",
    "📡 Connecting to TikTok servers...",
    "⚡ Initiating {service} delivery...",
    "🚀 Sending {amount} {service} to your account...",
    "⏳ Processing... {percent}% complete",
    "✅ Order completed successfully!"
]

# Error messages
ERROR_MESSAGES = {
    "private_account": "❌ Your TikTok account is private! Please make it public and try again.",
    "invalid_username": "❌ Invalid username! Please send your TikTok username (without @) or video link.",
    "cooldown_active": "⏳ Please wait! You can use this service again in {time_remaining}.",
    "max_daily_limit": "❌ Daily limit reached! Please try again tomorrow.",
    "service_down": "🔧 This service is temporarily under maintenance. Please try another service.",
    "invalid_link": "❌ Invalid TikTok link! Please send a valid TikTok video URL."
}
