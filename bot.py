import os
import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
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

# --- Channel Link ---
CHANNEL_LINK = "https://t.me/KooraPredict"

# --- Welcome Message in Arabic ---
WELCOME_TEXT = """
🌟 **مرحباً بك في بوت KooraPredict!** 🌟

⚽ **تابع توقعات مباريات اليوم**

📊 **ما نقدمه لك:**
• تحليلات احترافية
• إحصائيات دقيقة
• توقعات مدروسة للمباريات

🔥 **زر صفحتنا الآن وابق على اطلاع بكل جديد!**

اضغط على الزر أدناه للانضمام 👇
"""

# --- Button Text ---
BUTTON_TEXT = "📢 تابع توقعات مباريات اليوم - تحليلات احترافية"

# --- Image File Name ---
IMAGE_FILE = "image.png"

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with image and channel button."""
    user = update.effective_user
    logger.info(f"User {user.first_name} ({user.id}) started the bot.")

    # Create the inline keyboard button
    keyboard = [
        [InlineKeyboardButton(BUTTON_TEXT, url=CHANNEL_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        # Send image with caption and button
        with open(IMAGE_FILE, 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=WELCOME_TEXT,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
    except FileNotFoundError:
        logger.error(f"Image file '{IMAGE_FILE}' not found! Make sure it's in the bot directory.")
        # Fallback: send text only if image is missing
        await update.message.reply_text(
            WELCOME_TEXT,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error sending image: {e}")
        await update.message.reply_text(
            WELCOME_TEXT,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message."""
    help_text = """
🤖 **بوت KooraPredict**

⚽ **الأوامر المتاحة:**
/start - عرض رسالة الترحيب
/help - عرض هذه المساعدة

📢 **للاستفسار:** @Elgoumri1
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

# --- Error Handler ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")
    
    if isinstance(context.error, Conflict):
        logger.warning("Conflict error - another instance running")

# --- Main Function ---
def main():
    """Start the bot."""
    logger.info("🚀 Starting KooraPredict Bot...")
    
    # Check if image file exists
    if not os.path.exists(IMAGE_FILE):
        logger.warning(f"⚠️ '{IMAGE_FILE}' not found! The bot will work but without image.")
    else:
        logger.info(f"✅ Image file '{IMAGE_FILE}' found.")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add error handler
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
