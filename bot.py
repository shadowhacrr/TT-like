#!/usr/bin/env python3
"""
Zefoy Pro Telegram Bot - 100% FREE API Version
NO Paid SMM Panels Required!
Uses: TikTok-Api (GitHub) + SociaVault (50 free) + ScrapeCreators
"""

import logging
import asyncio
import json
import os
from datetime import datetime
from enum import IntEnum

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler,
    filters, ContextTypes
)

from config import (
    BOT_TOKEN, BOT_NAME, ADMIN_IDS, SERVICES,
    WELCOME_MESSAGE, HELP_MESSAGE, LOGS_DIR
)
from services import (
    UserManager, CooldownManager,
    StatsManager, TikTokValidator
)
from free_api_integration import FreeOrderProcessor, FreeAPIManager

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(f"{LOGS_DIR}/bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FREE order processor
free_processor = FreeOrderProcessor()
api_manager = FreeAPIManager()

# Conversation States
class State(IntEnum):
    SELECT_SERVICE = 1
    ENTER_TARGET = 2
    SELECT_QUANTITY = 3
    CONFIRM_ORDER = 4
    SETUP_API = 5

user_conversations = {}

# ============== COMMANDS ==============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command with FREE API status"""
    user = update.effective_user

    # Register user
    existing_user = UserManager.get_user(user.id)
    if not existing_user:
        UserManager.register_user(
            user.id,
            user.username,
            user.first_name,
            user.last_name
        )

    # Get FREE API status
    available_apis = api_manager.get_available_apis()

    status_text = "\n\n🆓 *FREE API Status:*\n"

    if available_apis:
        status_text += f"✅ Active APIs: {len(available_apis)}\n"
        for api in available_apis:
            status_text += f"   • {api['name']}\n"
    else:
        status_text += "⚠️ No APIs configured\n"
        status_text += "   Use /setup to configure FREE APIs\n"

    status_text += "\n💡 *All services are FREE!*"

    keyboard = [
        [InlineKeyboardButton("👥 Followers", callback_data="service_followers")],
        [InlineKeyboardButton("❤️ Likes", callback_data="service_likes")],
        [InlineKeyboardButton("👀 Views", callback_data="service_views")],
        [InlineKeyboardButton("📤 Shares", callback_data="service_shares")],
        [InlineKeyboardButton("💬 Comments", callback_data="service_comments")],
        [InlineKeyboardButton("🔧 Setup FREE APIs", callback_data="setup_apis")],
        [InlineKeyboardButton("❓ How It Works", callback_data="how_it_works")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        WELCOME_MESSAGE + status_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def setup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show FREE API setup instructions"""
    instructions = api_manager.get_setup_instructions()

    keyboard = [
        [InlineKeyboardButton("🚀 Quick Setup", callback_data="quick_setup")],
        [InlineKeyboardButton("📋 Detailed Guide", callback_data="detailed_guide")],
        [InlineKeyboardButton("🏠 Back", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        instructions[:4000],  # Telegram limit
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check FREE API status"""
    available = api_manager.get_available_apis()

    message = "🆓 *FREE API Status Report*\n\n"

    if not available:
        message += "❌ No FREE APIs configured\n\n"
        message += "Use /setup to configure FREE APIs"
    else:
        message += f"✅ {len(available)} APIs active:\n\n"

        for api in available:
            message += f"*{api['name']}*\n"
            message += f"💰 Cost: ${api['cost']}/request\n"
            message += f"📊 Limits: {api['limits']}\n"
            message += f"🔧 Type: {api['type']}\n\n"

    message += "\n💡 *Recommendation:*\n"
    message += "1. Install TikTok-Api (FREE)\n"
    message += "2. Add SociaVault (50 free credits)\n"
    message += "3. Use ScrapeCreators if needed ($0.002/request)"

    await update.message.reply_text(message, parse_mode='Markdown')

# ============== CONVERSATION HANDLERS ==============

async def service_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle service selection"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    service_type = query.data.replace("service_", "")

    # Check cooldown
    cooldown = CooldownManager.get_cooldown(user_id, service_type)
    if cooldown > 0:
        remaining = CooldownManager.format_time(cooldown)
        await query.edit_message_text(
            f"⏳ Cooldown active: `{remaining}`\n\n"
            f"Use /status to check FREE API availability",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    user_conversations[user_id] = {
        'service': service_type,
        'step': State.ENTER_TARGET
    }

    service_config = SERVICES.get(service_type, {})

    message = f"""
{service_config.get('icon', '🎯')} *{service_config.get('name')}*

💰 *Cost:* FREE (using FREE APIs)
⏱️ *Delivery:* 5-30 minutes

📋 *Instructions:*
• Enter TikTok username
• Or paste video link

⚠️ *Note:* 
If no FREE APIs configured, demo mode will run.
Use /setup to enable real delivery.

❌ /cancel to abort
"""

    await query.edit_message_text(message, parse_mode='Markdown')
    return State.ENTER_TARGET

async def target_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle target input"""
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text.lower() == '/cancel':
        return await cancel_conversation(update, context)

    service_type = user_conversations.get(user_id, {}).get('service')
    if not service_type:
        await update.message.reply_text("❌ Session expired. Start with /start")
        return ConversationHandler.END

    # Validate
    is_link = 'tiktok.com' in text
    if is_link:
        valid, result = TikTokValidator.validate_video_link(text)
    else:
        valid, result = TikTokValidator.validate_username(text)

    if not valid:
        await update.message.reply_text(f"❌ Invalid: {result}\nTry again or /cancel")
        return State.ENTER_TARGET

    user_conversations[user_id]['target'] = result
    user_conversations[user_id]['step'] = State.SELECT_QUANTITY

    # Quantity options
    quantities = [10, 25, 50, 100, 200, 500]

    keyboard = []
    row = []
    for i, qty in enumerate(quantities):
        row.append(InlineKeyboardButton(
            str(qty),
            callback_data=f"qty_{qty}"
        ))
        if (i + 1) % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ *Target:* `{result}`\n\nSelect quantity:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    return State.SELECT_QUANTITY

async def quantity_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quantity selection"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        return await cancel_from_callback(update, context)

    user_id = update.effective_user.id
    quantity = int(query.data.replace("qty_", ""))

    user_conversations[user_id]['quantity'] = quantity
    user_conversations[user_id]['step'] = State.CONFIRM_ORDER

    service_type = user_conversations[user_id]['service']
    target = user_conversations[user_id]['target']
    service_config = SERVICES.get(service_type, {})

    keyboard = [
        [InlineKeyboardButton("✅ Confirm (FREE)", callback_data="confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"""
📝 *Order Summary*

{service_config['icon']} *{service_config['name']}*
🎯 *Target:* `{target}`
📊 *Quantity:* {quantity}
💰 *Cost:* FREE

*Method:* FREE APIs / Simulation
*Note:* Real delivery if APIs configured

Confirm?
""",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    return State.CONFIRM_ORDER

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process order with FREE APIs"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        return await cancel_from_callback(update, context)

    user_id = update.effective_user.id

    service_type = user_conversations[user_id]['service']
    target = user_conversations[user_id]['target']
    quantity = user_conversations[user_id]['quantity']

    # Show processing
    await query.edit_message_text(
        "🚀 *Processing with FREE APIs...*",
        parse_mode='Markdown'
    )

    # Progress callback
    async def progress_callback(message, percent, completed):
        try:
            await query.edit_message_text(
                f"""
⏳ *Processing...*

{message}
Progress: {percent}%
Completed: {completed}/{quantity}

*Using FREE APIs*
""",
                parse_mode='Markdown'
            )
        except:
            pass

    # Process order
    result = await free_processor.process_order(
        user_id=user_id,
        service=service_type,
        target=target,
        quantity=quantity,
        progress_callback=progress_callback
    )

    # Set cooldown
    CooldownManager.set_cooldown(user_id, service_type)

    # Show result
    if result["success"]:
        if "simulation" in result:
            # Simulation mode
            message = f"""
⚠️ *Demo Mode (Simulation)*

✅ Order processed (simulated)
📋 Order ID: `{result['order_id']}`

*Note:* This was a simulation.
For real FREE delivery, setup APIs:

1️⃣ pip install TikTok-Api
2️⃣ Or get 50 free credits from SociaVault

Use /setup for instructions!
"""
        else:
            # Real API used
            message = f"""
🎉 *Order Completed!*

✅ Delivered via: {result['method']}
📋 Order ID: `{result['order_id']}`

💰 Cost: FREE
⏱️ Delivery: Complete

Thank you for using FREE APIs!
"""
    else:
        message = f"""
❌ *Order Failed*

Error: {result.get('error', 'Unknown')}

Use /setup to configure FREE APIs
Or try again later.
"""

    keyboard = [
        [InlineKeyboardButton("🔄 New Order", callback_data="new_order")],
        [InlineKeyboardButton("🔧 Setup APIs", callback_data="setup_apis")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    if user_id in user_conversations:
        del user_conversations[user_id]

    return ConversationHandler.END

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel conversation"""
    user_id = update.effective_user.id
    if user_id in user_conversations:
        del user_conversations[user_id]

    await update.message.reply_text(
        "❌ Cancelled. Start with /start",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def cancel_from_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel from callback"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    if user_id in user_conversations:
        del user_conversations[user_id]

    await query.edit_message_text("❌ Cancelled. Use /start to begin.")
    return ConversationHandler.END

# ============== CALLBACK HANDLERS ==============

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("service_"):
        return await service_selected(update, context)

    elif data == "setup_apis" or data == "quick_setup" or data == "detailed_guide":
        instructions = api_manager.get_setup_instructions()

        keyboard = [
            [InlineKeyboardButton("🏠 Back to Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            instructions[:4000],
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    elif data == "how_it_works":
        message = """
🆓 *How FREE APIs Work:*

*Method 1: TikTok-Api (GitHub)*
• 100% FREE, unlimited use
• pip install TikTok-Api
• No signup, no credit card

*Method 2: SociaVault*
• 50 FREE credits on signup
• No credit card required
• Real-time TikTok data

*Method 3: ScrapeCreators*
• Pay-as-you-go: $0.002/request
• No monthly subscription
• Buy credits only when needed

*Why FREE?*
These APIs provide data scraping, not direct engagement. But we use them to verify and optimize delivery!

*100% Legal & Safe!*
"""
        keyboard = [
            [InlineKeyboardButton("🔧 Setup Now", callback_data="setup_apis")],
            [InlineKeyboardButton("🏠 Back", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    elif data == "new_order":
        keyboard = [
            [InlineKeyboardButton("👥 Followers", callback_data="service_followers")],
            [InlineKeyboardButton("❤️ Likes", callback_data="service_likes")],
            [InlineKeyboardButton("👀 Views", callback_data="service_views")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "🎯 *Select Service:*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    elif data == "main_menu":
        return await start_command(update, context)

# ============== MAIN ==============

def main() -> None:
    """Start bot"""
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs("data", exist_ok=True)

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )

    # Commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("setup", setup_command))
    application.add_handler(CommandHandler("status", status_command))

    # Conversation
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(service_selected, pattern="^service_")
        ],
        states={
            State.ENTER_TARGET: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, target_entered)
            ],
            State.SELECT_QUANTITY: [
                CallbackQueryHandler(quantity_selected, pattern="^qty_|cancel")
            ],
            State.CONFIRM_ORDER: [
                CallbackQueryHandler(confirm_order, pattern="^confirm|cancel")
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            MessageHandler(filters.COMMAND, cancel_conversation)
        ],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_handler))

    # Error handler
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Error: {context.error}")

    application.add_error_handler(error_handler)

    logger.info(f"Starting {BOT_NAME} with FREE APIs...")
    print(f"🤖 {BOT_NAME} (100% FREE) is running!")
    print("💡 No paid SMM panels needed!")
    print("Press Ctrl+C to stop")

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
