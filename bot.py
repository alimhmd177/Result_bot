import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import config
from scraper import UniversityResultsScraper

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize scraper
scraper = UniversityResultsScraper(config.PORTAL_URL, config.DEFAULT_PASSWORD)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    welcome_message = """
🎓 *مرحباً بك في بوت نتائج جامعة البحر الأحمر*

📝 *كيفية الاستخدام:*
• أرسل رقمك الجامعي فقط وسأقوم بإحضار نتيجتك

💡 *مثال:*
`1124693617`

🔍 *الأوامر المتاحة:*
/start - عرض هذه الرسالة
/help - المساعدة
/about - معلومات عن البوت

📌 *ملاحظة:* تأكد من إدخال الرقم الجامعي بشكل صحيح
"""
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_message = """
❓ *المساعدة*

*كيفية استخدام البوت:*

1️⃣ أرسل رقمك الجامعي المكون من 10 أرقام
2️⃣ انتظر قليلاً حتى يتم استخراج النتيجة
3️⃣ ستحصل على نتيجتك كاملة مع جميع التفاصيل

*مثال على رقم جامعي صحيح:*
`1124693617`

*إذا واجهت مشكلة:*
• تأكد من أن الرقم الجامعي صحيح
• تأكد من أن الرقم مكون من 10 أرقام
• تأكد من عدم وجود مسافات في الرقم

📧 للدعم الفني، تواصل مع مطور البوت
"""
    await update.message.reply_text(
        help_message,
        parse_mode=ParseMode.MARKDOWN
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send information about the bot."""
    about_message = """
ℹ️ *معلومات عن البوت*

🤖 *اسم البوت:* بوت نتائج جامعة البحر الأحمر
📚 *الوظيفة:* استخراج نتائج الطلاب من بوابة الجامعة
🔒 *الأمان:* جميع البيانات آمنة ولا يتم حفظها

✨ *المميزات:*
• استخراج سريع للنتائج
• عرض جميع المواد والدرجات
• عرض المعدل الفصلي
• عرض حالة النجاح/الرسوب
• واجهة سهلة الاستخدام

🔧 *التقنيات المستخدمة:*
• Python
• python-telegram-bot
• BeautifulSoup4
• Requests

💻 *تم التطوير بواسطة:* Suna AI Agent
"""
    await update.message.reply_text(
        about_message,
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_university_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle university number and fetch results."""
    user_input = update.message.text.strip()
    
    # Validate university number (should be 10 digits)
    if not user_input.isdigit():
        await update.message.reply_text(
            "❌ الرجاء إدخال رقم جامعي صحيح (أرقام فقط)\n\n"
            "مثال: `1124693617`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if len(user_input) != 10:
        await update.message.reply_text(
            "❌ الرقم الجامعي يجب أن يكون مكوناً من 10 أرقام\n\n"
            "مثال: `1124693617`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "⏳ جاري استخراج النتيجة...\n"
        "الرجاء الانتظار قليلاً ⏰"
    )
    
    try:
        # Get results from scraper
        results = scraper.get_results(user_input)
        
        # Format and send results
        formatted_message = scraper.format_results_message(results)
        
        # Delete processing message
        await processing_msg.delete()
        
        # Send results
        await update.message.reply_text(
            formatted_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Log successful request
        logger.info(f"Results fetched successfully for: {user_input}")
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        await processing_msg.delete()
        await update.message.reply_text(
            "❌ حدث خطأ أثناء استخراج النتيجة\n"
            "الرجاء المحاولة مرة أخرى لاحقاً\n\n"
            "إذا استمرت المشكلة، تواصل مع الدعم الفني"
        )

async def handle_invalid_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle invalid input."""
    await update.message.reply_text(
        "❓ لم أفهم ما تريد\n\n"
        "الرجاء إرسال رقمك الجامعي فقط\n"
        "أو استخدم /help للمساعدة",
        parse_mode=ParseMode.MARKDOWN
    )

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    
    # Handle university numbers (10 digits)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_university_number
    ))

    # Log bot startup
    logger.info("Bot started successfully!")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()