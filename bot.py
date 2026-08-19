import os
import logging
import sys
import asyncio
import subprocess
import tempfile
import shutil
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
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
WELCOME_IMAGE = "image.png"

PREDICTION_IMAGES = [
    "prediction_1.jpg",
    "prediction_2.jpg",
    "prediction_3.jpg",
    "prediction_4.jpg",
    "prediction_5.jpg",
    "prediction_6.jpg",
    "prediction_7.jpg"
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

# --- Promo Sequence Messages ---
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

# --- Bot Mode ---
# "redirect" = Promo mode (welcome + sequence + images + channel)
# "reverse" = GIF mode (video to GIF converter)
bot_mode = "redirect"

# --- GIF Conversion Functions ---
def get_video_info(video_path):
    """Get video duration and dimensions using ffprobe."""
    try:
        cmd = [
            'ffprobe', '-v', 'error', '-show_entries',
            'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = float(result.stdout.strip()) if result.stdout else 0
        
        cmd = [
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            width, height = map(int, result.stdout.strip().split(','))
        else:
            width, height = 0, 0
        
        return {
            'duration': duration,
            'width': width,
            'height': height,
            'size_mb': os.path.getsize(video_path) / (1024 * 1024)
        }
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return None

def video_to_gif(video_path, output_path, fps=10, width=None, height=None, start_time=None, duration=None):
    """Convert video to GIF using ffmpeg."""
    try:
        cmd = ['ffmpeg', '-i', video_path]
        
        if start_time is not None:
            cmd.extend(['-ss', str(start_time)])
        
        if duration is not None:
            cmd.extend(['-t', str(duration)])
        
        if width and height:
            scale = f'scale={width}:{height}:flags=lanczos'
        elif width:
            scale = f'scale={width}:-1:flags=lanczos'
        elif height:
            scale = f'scale=-1:{height}:flags=lanczos'
        else:
            scale = 'scale=480:-1:flags=lanczos'
        
        cmd.extend([
            '-vf', scale,
            '-r', str(fps),
            '-f', 'gif',
            '-y',
            output_path
        ])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            return False, None, f"FFmpeg error: {result.stderr[:200]}"
        
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            return False, None, "Output file is empty."
        
        return True, output_path, None
        
    except subprocess.TimeoutExpired:
        return False, None, "Conversion timed out (max 2 minutes)."
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        return False, None, str(e)

# ============================================================
# REDIRECT MODE – Promo Functions
# ============================================================

async def send_promo_sequence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the full promo message sequence with images."""
    global bot_mode
    
    if bot_mode != "redirect":
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    try:
        # Message 1
        await context.bot.send_message(
            chat_id=chat_id,
            text=MESSAGE_1,
            parse_mode='Markdown'
        )
        logger.info(f"✅ Promo Message 1 sent to {user_id}")

        await asyncio.sleep(5)

        # Send all 7 images
        media_group = []
        caption_added = False

        for image_file in PREDICTION_IMAGES:
            try:
                if os.path.exists(image_file):
                    if not caption_added:
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
                else:
                    logger.warning(f"⚠️ Image file '{image_file}' not found")
            except Exception as e:
                logger.error(f"Error loading image {image_file}: {e}")

        if media_group:
            try:
                await context.bot.send_media_group(
                    chat_id=chat_id,
                    media=media_group
                )
                logger.info(f"✅ All promo images sent to {user_id}")
            except Exception as e:
                logger.error(f"Error sending media group: {e}")
                for img in PREDICTION_IMAGES:
                    if os.path.exists(img):
                        try:
                            with open(img, 'rb') as photo:
                                await context.bot.send_photo(chat_id=chat_id, photo=photo)
                            await asyncio.sleep(0.5)
                        except Exception as e2:
                            logger.error(f"Error sending {img}: {e2}")
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ الصور غير متوفرة حالياً"
            )

        await asyncio.sleep(3)

        # Message 2
        await context.bot.send_message(
            chat_id=chat_id,
            text=MESSAGE_2,
            parse_mode='Markdown'
        )
        logger.info(f"✅ Promo Message 2 sent to {user_id}")

        await asyncio.sleep(2)

        # Message 3
        await context.bot.send_message(
            chat_id=chat_id,
            text=MESSAGE_3,
            parse_mode='Markdown'
        )
        logger.info(f"✅ Promo Message 3 sent to {user_id}")

        # Schedule delayed messages
        job_queue = context.job_queue
        if job_queue:
            job_queue.run_once(
                send_delayed_promo_message,
                when=360,
                data={'chat_id': chat_id, 'user_id': user_id, 'message': MESSAGE_4, 'type': 'message_4'}
            )
            job_queue.run_once(
                send_delayed_promo_message,
                when=1800,
                data={'chat_id': chat_id, 'user_id': user_id, 'message': MESSAGE_5, 'type': 'message_5'}
            )
            logger.info(f"⏰ Scheduled promo messages for {user_id}")

    except Exception as e:
        logger.error(f"Error in promo sequence: {e}")

async def send_delayed_promo_message(context: ContextTypes.DEFAULT_TYPE):
    """Send a delayed promo message."""
    global bot_mode
    
    if bot_mode != "redirect":
        return

    data = context.job.data
    chat_id = data['chat_id']
    user_id = data['user_id']
    message = data['message']

    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='Markdown'
        )
        logger.info(f"✅ Delayed promo message sent to {user_id}")
    except Exception as e:
        logger.error(f"Error sending delayed promo message: {e}")

# ============================================================
# REVERSE MODE – GIF Converter Functions
# ============================================================

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video messages for GIF conversion (REVERSE mode)."""
    global bot_mode
    
    if bot_mode != "reverse":
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Check for video
    video = update.message.video
    if not video:
        await update.message.reply_text("❌ Please send a video file!")
        return

    MAX_FILE_SIZE = 50 * 1024 * 1024
    if video.file_size > MAX_FILE_SIZE:
        await update.message.reply_text(
            f"❌ Video too large! Max 50MB.\nSize: {video.file_size / (1024*1024):.1f}MB"
        )
        return

    processing_msg = await update.message.reply_text("⏳ Converting video to GIF...")
    
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, 'input_video.mp4')
        output_path = os.path.join(temp_dir, 'output.gif')
        
        file = await context.bot.get_file(video.file_id)
        await file.download_to_drive(video_path)
        
        # Get video info
        video_info = get_video_info(video_path)
        if video_info:
            await processing_msg.edit_text(
                f"⏳ Converting...\nDuration: {video_info['duration']:.1f}s"
            )
        
        # Convert to GIF
        success, output_path, error = video_to_gif(
            video_path, output_path,
            fps=10,
            width=480,
            height=None
        )
        
        if not success:
            await processing_msg.edit_text(f"❌ Conversion failed: {error}")
            return
        
        output_size = os.path.getsize(output_path) / (1024 * 1024)
        
        with open(output_path, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename='converted.gif',
                caption=(
                    f"✅ **GIF Created!**\n\n"
                    f"📊 Size: {output_size:.2f}MB\n"
                    f"📐 FPS: 10\n"
                    f"⚡ Mode: REVERSE (GIF Converter)"
                ),
                parse_mode='Markdown'
            )
        
        await processing_msg.delete()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await processing_msg.edit_text("❌ Error processing video. Please try again.")
    
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

# ============================================================
# COMMAND HANDLERS
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the bot based on current mode."""
    global bot_mode
    user = update.effective_user
    user_id = user.id
    logger.info(f"User {user.first_name} ({user_id}) started the bot. Mode: {bot_mode.upper()}")

    if bot_mode == "redirect":
        await start_redirect_mode(update, context)
    else:
        await start_reverse_mode(update, context)

async def start_redirect_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the bot in REDIRECT (promo) mode."""
    user = update.effective_user
    user_id = user.id
    chat_id = update.effective_chat.id

    keyboard = [
        [InlineKeyboardButton(BUTTON_TEXT, url=CHANNEL_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

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
            await update.message.reply_text(
                WELCOME_TEXT,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error sending welcome: {e}")
        await update.message.reply_text(
            WELCOME_TEXT,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    await asyncio.sleep(1)
    await send_promo_sequence(update, context)

async def start_reverse_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the bot in REVERSE (GIF converter) mode."""
    await update.message.reply_text(
        "🎬 **وضع تحويل الفيديو إلى GIF**\n\n"
        "📤 أرسل لي فيديو وسأقوم بتحويله إلى GIF!\n\n"
        "📌 **الميزات:**\n"
        "• تحويل فيديو إلى GIF متحرك\n"
        "• دعم حتى 50 ميجابايت\n"
        "• جودة عالية\n\n"
        "🔄 استخدم /redirect للعودة إلى الوضع العادي.",
        parse_mode='Markdown'
    )

# ============================================================
# REVERSE COMMAND – Switch to GIF mode
# ============================================================
async def reverse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Switch to REVERSE (GIF converter) mode."""
    global bot_mode
    user = update.effective_user
    user_id = user.id

    if bot_mode == "reverse":
        await update.message.reply_text(
            "🔄 **البوت بالفعل في وضع تحويل الفيديو إلى GIF!**\n\n"
            "📤 أرسل لي فيديو للتحويل.",
            parse_mode='Markdown'
        )
        return

    bot_mode = "reverse"
    logger.info(f"🔄 Bot switched to REVERSE (GIF) mode by user {user_id}")

    await update.message.reply_text(
        "🎬 **تم التبديل إلى وضع تحويل الفيديو إلى GIF!**\n\n"
        "📤 أرسل لي فيديو وسأقوم بتحويله إلى GIF!\n\n"
        "📌 **الميزات:**\n"
        "• تحويل فيديو إلى GIF متحرك\n"
        "• دعم حتى 50 ميجابايت\n"
        "• جودة عالية\n\n"
        "🔁 استخدم /redirect للعودة إلى الوضع العادي.",
        parse_mode='Markdown'
    )

# ============================================================
# REDIRECT COMMAND – Switch to Promo mode
# ============================================================
async def redirect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Switch to REDIRECT (promo) mode."""
    global bot_mode
    user = update.effective_user
    user_id = user.id

    if bot_mode == "redirect":
        await update.message.reply_text(
            "🔁 **البوت بالفعل في الوضع العادي!**\n\n"
            "استخدم /start لعرض رسالة الترحيب.",
            parse_mode='Markdown'
        )
        return

    bot_mode = "redirect"
    logger.info(f"🔁 Bot switched to REDIRECT (promo) mode by user {user_id}")

    await update.message.reply_text(
        "🔁 **تم التبديل إلى الوضع العادي!**\n\n"
        "✅ البوت الآن يعمل بالوضع الطبيعي.\n"
        "✅ سيتم إرسال الرسائل التسويقية والصور.\n\n"
        "استخدم /start لبدء التجربة!",
        parse_mode='Markdown'
    )

# ============================================================
# STATUS COMMAND
# ============================================================
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the current bot mode."""
    global bot_mode

    if bot_mode == "redirect":
        mode_text = "🔁 **الوضع العادي** (REDIRECT) - رسائل تسويقية"
        description = "يقوم البوت بإرسال رسائل الترحيب والصور التسويقية."
    else:
        mode_text = "🎬 **وضع تحويل الفيديو إلى GIF** (REVERSE)"
        description = "يقوم البوت بتحويل الفيديوهات إلى GIF."

    status = f"""
📊 **حالة البوت**

{mode_text}

📌 **الوصف:** {description}

📋 **الأوامر المتاحة:**
/start - بدء البوت حسب الوضع الحالي
/reverse - تفعيل وضع تحويل الفيديو إلى GIF
/redirect - تفعيل الوضع العادي (الرسائل التسويقية)
/status - عرض حالة البوت
/help - عرض المساعدة
    """

    await update.message.reply_text(status, parse_mode='Markdown')

# ============================================================
# HELP COMMAND
# ============================================================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message."""
    help_text = """
🤖 **بوت KooraPredict**

📌 **الوضعان المتاحان:**

🔹 **الوضع العادي (REDIRECT):**
• يقوم البوت بإرسال رسائل الترحيب
• يعرض الصور التسويقية
• يوجه المستخدم إلى القناة

🔸 **وضع تحويل الفيديو إلى GIF (REVERSE):**
• يقوم البوت بتحويل الفيديوهات إلى GIF
• يدعم حتى 50 ميجابايت
• جودة عالية

⚽ **الأوامر المتاحة:**
/start - بدء البوت حسب الوضع الحالي
/reverse - تفعيل وضع تحويل الفيديو إلى GIF
/redirect - تفعيل الوضع العادي
/status - عرض حالة البوت
/help - عرض هذه المساعدة

📢 **للاستفسار:** @Elgoumri1
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ============================================================
# ERROR HANDLER
# ============================================================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")

    if isinstance(context.error, Conflict):
        logger.warning("Conflict error - another instance running")

# ============================================================
# MAIN FUNCTION
# ============================================================
def main():
    """Start the bot."""
    global bot_mode
    logger.info("🚀 Starting KooraPredict Bot...")
    logger.info(f"📌 Initial mode: {bot_mode.upper()}")

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

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reverse", reverse_command))
    application.add_handler(CommandHandler("redirect", redirect_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("help", help_command))

    # Video handler for REVERSE mode (GIF conversion)
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))

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
