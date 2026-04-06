# 🤖 Zefoy Pro Telegram Bot

A file-based TikTok growth automation bot for Telegram, inspired by Zefoy.com. No database required - everything stored in JSON files!

## ✨ Features

- **5 Services**: Followers, Likes, Views, Shares, Comments
- **File-Based Storage**: No database setup needed (JSON files)
- **Cooldown System**: Prevents spam with per-service cooldowns
- **Order Tracking**: Complete order history for users
- **Admin Panel**: Stats, user management, broadcast
- **Simulated Processing**: Real-time progress updates
- **Responsive UI**: Inline keyboards and smooth navigation

## 📁 File Structure

```
zefoy_bot/
├── bot.py              # Main bot file
├── config.py           # Configuration & messages
├── services.py         # Core logic & file storage
├── requirements.txt    # Dependencies
├── data/               # JSON storage (auto-created)
│   ├── users.json      # User data
│   ├── orders.json     # Order history
│   ├── cooldowns.json  # Cooldown tracking
│   └── stats.json      # Bot statistics
└── logs/               # Log files (auto-created)
    └── bot.log
```

## 🚀 Setup Instructions

### 1. Get Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow instructions to create bot
4. Copy the **API Token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Install Dependencies

```bash
# Create virtual environment (optional but recommended)
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Configure Bot

Edit `config.py`:

```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Paste your token from BotFather
ADMIN_IDS = [123456789]  # Your Telegram user ID (get from @userinfobot)
```

### 4. Run Bot

```bash
python bot.py
```

You should see: `🤖 ZefoyProBot is running...`

## 🎯 How to Use

### User Flow:
1. Send `/start` to bot
2. Click service button (Followers/Likes/Views)
3. Enter TikTok username or video link
4. Select quantity
5. Confirm order
6. Watch real-time processing
7. Receive success confirmation

### Admin Commands:
- `/admin` - Open admin panel
- `/stats` - View bot statistics

## ⚙️ Configuration

### Services (in config.py):
```python
SERVICES = {
    "followers": {
        "name": "👥 Followers",
        "min": 100,
        "max": 10000,
        "cooldown": 3600,  # 1 hour
    },
    # ... more services
}
```

### Cooldown Times:
- Views: 15 minutes
- Likes: 30 minutes
- Followers: 1 hour
- Shares: 1 hour
- Comments: 2 hours

## 📊 Data Files

All data stored in `data/` folder as JSON:

- **users.json**: User profiles, join dates, order counts
- **orders.json**: Complete order history
- **cooldowns.json**: User cooldown timestamps
- **stats.json**: Bot-wide statistics

## 🔧 Customization

### Change Messages:
Edit `WELCOME_MESSAGE`, `HELP_MESSAGE`, etc. in `config.py`

### Add Services:
1. Add entry in `SERVICES` dict in `config.py`
2. Add service button in `bot.py` keyboard
3. Update cooldown logic if needed

### Real Integration:
To make it actually deliver (not simulated):
1. Replace `OrderSimulator` class in `services.py`
2. Add real TikTok API integration or third-party SMM panel API
3. Update order status tracking

## 📝 Commands

| Command | Description |
|---------|-------------|
| `/start` | Start bot / Main menu |
| `/help` | Show help message |
| `/stats` | Bot statistics |
| `/admin` | Admin panel (admin only) |
| `/cancel` | Cancel current order |

## 🛡️ Safety Features

- Username validation
- Link validation
- Cooldown enforcement
- Order confirmation step
- Session cleanup
- Error handling

## 🐛 Troubleshooting

**Bot not responding?**
- Check if token is correct in `config.py`
- Ensure internet connection
- Check `logs/bot.log` for errors

**"Session expired" error?**
- User took too long, start again with `/start`

**Cooldown not working?**
- Check `data/cooldowns.json` file permissions

## 📞 Support

For issues or questions:
1. Check logs in `logs/bot.log`
2. Verify JSON files in `data/` folder
3. Ensure Python 3.8+ is installed

## ⚠️ Disclaimer

This bot is for **educational purposes**. Simulated delivery only.
For real TikTok growth, you need:
- Official TikTok API access (rare)
- Third-party SMM panel integration
- Compliance with TikTok ToS

## 📄 License

MIT License - Free to use and modify!

---

**Made with ❤️ for the TikTok growth community**
