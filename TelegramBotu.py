from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
import asyncio

# Logging ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = "7806413438:AAGao-5vJdpxxydutLHE_tl6rSIFm9MUeb4"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot /start komutu alınca çalışacak fonksiyon"""
    await update.message.reply_text(
        f"👋 Merhaba {update.effective_user.first_name}!\n"
        "Hoş geldin! Ben Zethara botuyum."
    )

async def main():
    """Ana fonksiyon"""
    # Bot uygulamasını başlat
    application = Application.builder().token(TOKEN).build()

    # /start komutunu ekle
    application.add_handler(CommandHandler("start", start))

    # Botu başlat
    logger.info("Bot başlatılıyor...")
    await application.initialize()
    await application.start()
    await application.run_polling(allowed_updates=Update.ALL_TYPES)
    await application.stop()

def run_bot():
    """Botu çalıştır"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot durduruldu")
    except Exception as e:
        logger.error(f"Kritik hata: {e}")

if __name__ == "__main__":
    run_bot()
