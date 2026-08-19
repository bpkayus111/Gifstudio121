import os
import logging
import sys
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from telegram.error import Conflict

# --- Configuration ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("BOT_TOKEN environment variable not set!")
    sys.exit(1)

# --- Enable Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Global Bot Mode ---
# "LOGO" = Normal mode (Logo Maker)
# "REDIRECT" = Funnel mode (Redirects to channel)
GLOBAL_BOT_MODE = "LOGO"

# --- Channel Link for REDIRECT Mode ---
CHANNEL_LINK = "https://t.me/KooraPredict"
CHANNEL_BUTTON_TEXT = "📢 انضم إلى قناتنا الآن"

# --- Normal Mode Welcome Message ---
NORMAL_WELCOME = """
👋 *مرحباً بك في بوت KooraPredict!*

🎨 *أنا بوت متخصص في:*
• تحليلات كرة القدم
• توقعات المباريات
• إحصائيات دقيقة

📌 *كيفية الاستخدام:*
أرسل لي اسم الفريق أو المباراة وسأقدم لك التحليلات.

🔧 *الأوامر المتاحة:*
/start - عرض هذه الرسالة
/help - عرض المساعدة
/cancel - إلغاء العملية الحالية
"""

# --- REDIRECT Mode Welcome Message ---
REDIRECT_WELCOME = """
🌟 *مرحباً بك!*

💰 *في عالم عدم اليقين الاقتصادي، الحصول على دخل سلبي هو الحل.*

📊 *نقدم لك توقعات دقيقة لمباريات اليوم مع تحليلات احترافية.*

🔥 *انضم إلى قناتنا الآن وابدأ رحلة الربح!*

اضغط على الزر أدناه للانضمام 👇
"""

# --- User State Storage ---
user_sessions = {}

# ============================================================
# KEYBOARD MARKUP FUNCTIONS
# ============================================================

def main_menu_markup():
    """Main menu keyboard for normal mode."""
    keyboard = [
        [InlineKeyboardButton("🎨 Create Logo", callback_data="create_logo")],
        [InlineKeyboardButton("📊 My Logos", callback_data="my_logos")],
        [InlineKeyboardButton("❓ Help", callback_data="help_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============================================================
# COMMAND HANDLERS
# ============================================================

async def start_command(update: Update, context: CallbackContext):
    """Start command - checks mode and responds accordingly."""
    global GLOBAL_BOT_MODE
    user = update.effective_user
    user_id = user.id
    logger.info(f"User {user.first_name} ({user_id}) started bot. Mode: {GLOBAL_BOT_MODE}")

    # Reset user state
    if user_id in user_sessions:
        user_sessions[user_id] = {}

    # --- REDIRECT MODE ---
    if GLOBAL_BOT_MODE == "REDIRECT":
        # Send welcome text
        await update.message.reply_text(
            REDIRECT_WELCOME,
            parse_mode='Markdown'
        )

        # Small delay for dramatic effect
        await asyncio.sleep(1)

        # Send channel button
        keyboard = [
            [InlineKeyboardButton(CHANNEL_BUTTON_TEXT, url=CHANNEL_LINK)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🔗 *اضغط هنا للانضمام إلى القناة:*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return

    # --- NORMAL MODE (LOGO) ---
    await update.message.reply_text(
        NORMAL_WELCOME,
        parse_mode='Markdown',
        reply_markup=main_menu_markup()
    )

# ============================================================
# TEXT HANDLER – Intercepts REDIRECT/REVERSE commands
# ============================================================

async def handle_text(update: Update, context: CallbackContext):
    """Handle all text messages - intercepts secret commands."""
    global GLOBAL_BOT_MODE

    if not update.message or not update.message.text:
        return

    user = update.effective_user
    user_id = user.id
    text = update.message.text.strip()

    logger.info(f"Text received from {user_id}: {text}")

    # ============================================================
    # SECRET ADMIN COMMANDS – Intercept these first
    # ============================================================

    # Command: REDIRECT – Activate funnel mode
    if text == "REDIRECT":
        GLOBAL_BOT_MODE = "REDIRECT"
        logger.info(f"🔁 Mode changed to REDIRECT by {user_id}")
        await update.message.reply_text(
            "✅ *Redirect mode activated!*\n\n"
            "The bot will now redirect users to the channel.\n"
            "Send *REVERSE* to return to normal mode.",
            parse_mode='Markdown'
        )
        return

    # Command: REVERSE – Return to normal mode
    if text == "REVERSE":
        GLOBAL_BOT_MODE = "LOGO"
        logger.info(f"🔄 Mode changed to LOGO by {user_id}")
        await update.message.reply_text(
            "✅ *Normal mode activated!*\n\n"
            "The bot is now in Logo Maker mode.\n"
            "Send *REDIRECT* to activate funnel mode.",
            parse_mode='Markdown'
        )
        return

    # ============================================================
    # If in REDIRECT mode, ignore all other text
    # ============================================================
    if GLOBAL_BOT_MODE == "REDIRECT":
        logger.info(f"Ignoring text from {user_id} (REDIRECT mode active)")
        return

    # ============================================================
    # NORMAL MODE – Process text for Logo Maker
    # ============================================================

    # Initialize user session if needed
    if user_id not in user_sessions:
        user_sessions[user_id] = {}

    # Check if user is in logo creation flow
    if user_sessions[user_id].get('step') == 'awaiting_brand_name':
        # Process brand name
        brand_name = text
        user_sessions[user_id]['brand_name'] = brand_name
        user_sessions[user_id]['step'] = 'awaiting_slogan'

        await update.message.reply_text(
            f"✅ Great! Brand name: *{brand_name}*\n\n"
            "Now send me a short *slogan* or *tagline* for your logo.\n"
            "Example: 'Quality You Can Trust'\n\n"
            "Or send /cancel to stop.",
            parse_mode='Markdown'
        )
        return

    if user_sessions[user_id].get('step') == 'awaiting_slogan':
        # Process slogan
        slogan = text
        brand_name = user_sessions[user_id].get('brand_name', 'Brand')
        user_sessions[user_id] = {}

        # Generate logo response
        logo_preview = f"""
🎨 *Logo Generated!*

🏷️ *Brand:* {brand_name}
📝 *Slogan:* {slogan}

📐 *Design Details:*
• Clean, modern typography
• Professional color scheme
• Scalable vector design

✅ *Your logo is ready!*
Would you like to:
• Download high-res version
• Edit colors
• Add icon
"""
        keyboard = [
            [InlineKeyboardButton("📥 Download Logo", callback_data="download_logo")],
            [InlineKeyboardButton("🎨 Edit Design", callback_data="edit_logo")],
            [InlineKeyboardButton("🔄 Start Over", callback_data="create_logo")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            logo_preview,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

        # Reset user session
        user_sessions[user_id] = {}
        return

    # Default response for normal mode
    await update.message.reply_text(
        "🤔 I didn't understand that.\n\n"
        "Use /start to begin creating a logo!\n"
        "Or send /help for assistance.",
        parse_mode='Markdown'
    )

# ============================================================
# CALLBACK QUERY HANDLER
# ============================================================

async def menu_callback(update: Update, context: CallbackContext):
    """Handle inline keyboard button presses."""
    global GLOBAL_BOT_MODE

    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id
    data = query.data

    # --- If in REDIRECT mode, ignore all callbacks ---
    if GLOBAL_BOT_MODE == "REDIRECT":
        logger.info(f"Ignoring callback from {user_id} (REDIRECT mode active)")
        await query.edit_message_text(
            "⚠️ The bot is currently in redirect mode.\n"
            "Please try again later.",
            parse_mode='Markdown'
        )
        return

    # --- NORMAL MODE – Process callbacks ---
    if data == "create_logo":
        user_sessions[user_id] = {'step': 'awaiting_brand_name'}
        await query.edit_message_text(
            "🎨 *Let's create your logo!*\n\n"
            "Please send me your *brand name* first.\n"
            "Example: 'Apple', 'Nike', 'Starbucks'\n\n"
            "Send /cancel to stop.",
            parse_mode='Markdown'
        )

    elif data == "my_logos":
        await query.edit_message_text(
            "📊 *Your Logo History*\n\n"
            "You haven't created any logos yet.\n\n"
            "Click 'Create Logo' to start!",
            parse_mode='Markdown',
            reply_markup=main_menu_markup()
        )

    elif data == "help_menu":
        help_text = """
❓ *Help Menu*

📌 *How to create a logo:*
1. Click 'Create Logo'
2. Send your brand name
3. Send your slogan
4. Get your logo!

🔧 *Commands:*
/start - Main menu
/help - This help
/cancel - Cancel current operation

📢 *Need support?*
Contact @SupportBot
"""
        await query.edit_message_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=main_menu_markup()
        )

    elif data == "download_logo":
        await query.edit_message_text(
            "📥 *Download Logo*\n\n"
            "Your logo is being prepared for download...\n\n"
            "🔗 [Download Link](https://example.com/logo.png)\n\n"
            "Would you like to make another logo?",
            parse_mode='Markdown',
            reply_markup=main_menu_markup()
        )

    elif data == "edit_logo":
        await query.edit_message_text(
            "🎨 *Edit Logo*\n\n"
            "Choose what to edit:\n\n"
            "• 🎨 Change Colors\n"
            "• 📝 Edit Text\n"
            "• 🖼️ Add Icon\n"
            "• 📐 Change Layout",
            parse_mode='Markdown',
            reply_markup=main_menu_markup()
        )

    else:
        await query.edit_message_text(
            "Unknown option. Please try again.",
            reply_markup=main_menu_markup()
        )

# ============================================================
# HELP COMMAND
# ============================================================

async def help_command(update: Update, context: CallbackContext):
    """Help command."""
    global GLOBAL_BOT_MODE

    if GLOBAL_BOT_MODE == "REDIRECT":
        await update.message.reply_text(
            "⚠️ The bot is currently in redirect mode.\n"
            "Please try again later.",
            parse_mode='Markdown'
        )
        return

    help_text = """
🤖 *KooraPredict Bot Help*

📌 *Commands:*
/start - Start the bot
/help - Show this help
/cancel - Cancel current operation

🎨 *How to use:*
1. Click 'Create Logo'
2. Send your brand name
3. Send your slogan
4. Get your logo!

📢 *Support:* @Elgoumri1
"""
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=main_menu_markup()
    )

# ============================================================
# CANCEL COMMAND
# ============================================================

async def cancel_command(update: Update, context: CallbackContext):
    """Cancel current operation."""
    global GLOBAL_BOT_MODE

    if GLOBAL_BOT_MODE == "REDIRECT":
        await update.message.reply_text(
            "⚠️ The bot is currently in redirect mode.\n"
            "Please try again later.",
            parse_mode='Markdown'
        )
        return

    user_id = update.effective_user.id

    if user_id in user_sessions:
        user_sessions[user_id] = {}
        await update.message.reply_text(
            "✅ *Operation cancelled!*\n\n"
            "You can start again with /start",
            parse_mode='Markdown',
            reply_markup=main_menu_markup()
        )
    else:
        await update.message.reply_text(
            "ℹ️ No active operation to cancel.",
            reply_markup=main_menu_markup()
        )

# ============================================================
# STATUS COMMAND – Show current mode (Admin only)
# ============================================================

async def status_command(update: Update, context: CallbackContext):
    """Show current bot mode."""
    global GLOBAL_BOT_MODE

    user_id = update.effective_user.id

    # Only allow admins (optional - you can add admin list)
    status = f"""
📊 *Bot Status*

🔹 *Current Mode:* {GLOBAL_BOT_MODE}

📌 *Description:*
{'• Redirecting users to channel' if GLOBAL_BOT_MODE == 'REDIRECT' else '• Logo Maker mode active'}

💡 *Commands:*
• Send *REDIRECT* to activate funnel mode
• Send *REVERSE* to return to normal mode
"""
    await update.message.reply_text(
        status,
        parse_mode='Markdown'
    )

# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(update: object, context: CallbackContext):
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")

    if isinstance(context.error, Conflict):
        logger.warning("Conflict error - another instance running")

# ============================================================
# MAIN FUNCTION
# ============================================================

def main():
    """Start the bot."""
    global GLOBAL_BOT_MODE

    logger.info("🚀 Starting KooraPredict Bot...")
    logger.info(f"📌 Initial mode: {GLOBAL_BOT_MODE}")

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("status", status_command))

    # Text handler (intercepts REDIRECT/REVERSE)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Callback handler
    application.add_handler(CallbackQueryHandler(menu_callback))

    # Error handler
    application.add_error_handler(error_handler)

    logger.info("✅ Bot is ready!")

    # Start the bot
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except Conflict as e:
        logger.error(f"Conflict error: {e}")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
