import os
import logging
import sys
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
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

# --- Image Files ---
WELCOME_IMAGE = "welcome.png"

PREDICTION_IMAGES = [
    "prediction_1.jpg",
    "prediction_2.jpg",
    "prediction_3.jpg",
    "prediction_4.jpg",
    "prediction_5.jpg",
    "prediction_6.jpg",
]

# --- Welcome Message ---
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

BUTTON_TEXT = "📢 تابع توقعات مباريات اليوم - تحليلات احترافية"

# --- Sequence Messages ---
MESSAGE_1 = """👋 **مرحباً!** سعيد برؤيتك هنا.

دعنا لا نضيع الوقت ونذهب مباشرة إلى النقطة!"""

MESSAGE_2 = """🎯 **إذا كنت تراسلني**، فأنت تبحث بوضوح عن طريقة مثبتة للربح من خلال توقعات كرة القدم.

📊 **مجتمعي** يتكون من أكثر من 6,200 متداول انتقلوا من "المحاولة" إلى "الربح" كل يوم.

🔥 **سأريك بالضبط كيف يفعلون ذلك!**"""

MESSAGE_3 = """📝 **لنبدأ، أحتاج إلى معرفة من أعمل معه:**

❓ **هل لديك أي خبرة سابقة في كرة القدم؟**"""

MESSAGE_4 = """⏳ **لقد رأيت الرسالة - هل تريد البدء أم لا تزال تفكر؟**"""

MESSAGE_5 = """💪 **لا تقلق إذا كنت جديداً!**

أنا أرشد الجميع خطوة بخطوة، لذلك لن تكون بمفردك. 🚀"""

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with image and channel button."""
    user = update.effective_user
    user_id = user.id
    logger.info(f"User {user.first_name} ({user_id}) started the bot.")

    # Create the inline keyboard button
    keyboard = [
        [InlineKeyboardButton(BUTTON_TEXT, url=CHANNEL_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # ============================================================
    # STEP 1: Send Welcome Image with Message and Button
    # ============================================================
    try:
        if os.path.exists(WELCOME_IMAGE):
            with open(WELCOME_IMAGE, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=WELCOME_TEXT,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            logger.info(f"✅ Welcome image sent to {user_id}")
        else:
            logger.error(f"❌ Welcome image '{WELCOME_IMAGE}' not found!")
            await update.message.reply_text(
                WELCOME_TEXT,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error sending welcome image: {e}")
        await update.message.reply_text(
            WELCOME_TEXT,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    # Start the sequence after the welcome message
    await asyncio.sleep(1)
    await send_sequence(update, context)

async def send_sequence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the full message sequence with images."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    try:
        # ============================================================
        # STEP 2: Send Message 1
        # ============================================================
        await context.bot.send_message(
            chat_id=chat_id,
            text=MESSAGE_1,
            parse_mode='Markdown'
        )
        logger.info(f"✅ Message 1 sent to {user_id}")

        # Wait 5 seconds
        await asyncio.sleep(5)

        # ============================================================
        # STEP 3: Send ALL 7 images at once (as an album)
        # ============================================================
        media_group = []
        caption_added = False

        for image_file in PREDICTION_IMAGES:
            try:
                if os.path.exists(image_file):
                    if not caption_added:
                        # First image gets the caption
                        media_group.append(
                            InputMediaPhoto(
                                media=open(image_file, 'rb'),
                                caption="📊 **توقعات اليوم - KooraPredict**",
                                parse_mode='Markdown'
                            )
                        )
                        caption_added = True
                    else:
                        media_group.append(
                            InputMediaPhoto(media=open(image_file, 'rb'))
                        )
                    logger.info(f"✅ Added {image_file} to media group")
                else:
                    logger.warning(f"⚠️ Image file '{image_file}' not found")
            except Exception as e:
                logger.error(f"Error loading image {image_file}: {e}")

        # Send all images as an album
        if media_group:
            try:
                await context.bot.send_media_group(
                    chat_id=chat_id,
                    media=media_group
                )
                logger.info(f"✅ All {len(media_group)} images sent to {user_id}")
            except Exception as e:
                logger.error(f"Error sending media group: {e}")
                # Fallback: send images one by one
                for img in PREDICTION_IMAGES:
                    if os.path.exists(img):
                        try:
                            with open(img, 'rb') as photo:
                                await context.bot.send_photo(
                                    chat_id=chat_id,
                                    photo=photo
                                )
                            await asyncio.sleep(0.5)
                        except Exception as e2:
                            logger.error(f"Error sending {img}: {e2}")
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ الصور غير متوفرة حالياً"
            )

        # Wait 3 seconds after images
        await asyncio.sleep(3)

        # ============================================================
        # STEP 4: Send Message 3
        # ============================================================
        await context.bot.send_message(
            chat_id=chat_id,
            text=MESSAGE_3,
            parse_mode='Markdown'
        )
        logger.info(f"✅ Message 3 sent to {user_id}")

        # ============================================================
        # STEP 5: Schedule Message 4 (6 minutes later)
        # ============================================================
        job_queue = context.job_queue
        if job_queue:
            job_queue.run_once(
                send_delayed_message,
                when=360,  # 6 minutes
                data={
                    'chat_id': chat_id,
                    'user_id': user_id,
                    'message': MESSAGE_4,
                    'type': 'message_4'
                }
            )
            logger.info(f"⏰ Scheduled message 4 for {user_id} in 6 minutes")

            # ============================================================
            # STEP 6: Schedule Message 5 (24 minutes after Message 4)
            # ============================================================
            job_queue.run_once(
                send_delayed_message,
                when=1800,  # 30 minutes total
                data={
                    'chat_id': chat_id,
                    'user_id': user_id,
                    'message': MESSAGE_5,
                    'type': 'message_5'
                }
            )
            logger.info(f"⏰ Scheduled message 5 for {user_id} in 30 minutes")
        else:
            logger.warning("⚠️ Job queue not available - delayed messages won't work")

    except Exception as e:
        logger.error(f"Error in sequence: {e}")

async def send_delayed_message(context: ContextTypes.DEFAULT_TYPE):
    """Send a delayed message."""
    data = context.job.data
    chat_id = data['chat_id']
    user_id = data['user_id']
    message = data['message']
    msg_type = data.get('type', 'unknown')

    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='Markdown'
        )
        logger.info(f"✅ {msg_type} sent to {user_id}")
    except Exception as e:
        logger.error(f"Error sending {msg_type} to {user_id}: {e}")

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

    # Check files
    if os.path.exists(WELCOME_IMAGE):
        logger.info(f"✅ Welcome image found: {WELCOME_IMAGE}")
    else:
        logger.warning(f"⚠️ '{WELCOME_IMAGE}' not found!")

    found = [img for img in PREDICTION_IMAGES if os.path.exists(img)]
    missing = [img for img in PREDICTION_IMAGES if not os.path.exists(img)]
    if found:
        logger.info(f"✅ Found {len(found)} prediction images")
    if missing:
        logger.warning(f"⚠️ Missing images: {missing}")

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
