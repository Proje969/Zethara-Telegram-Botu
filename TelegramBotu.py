from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CommandHandler, CallbackQueryHandler
import asyncio
import json
import aiohttp
import os
from datetime import datetime
import pytz
from typing import List, Dict
import requests
from requests.exceptions import RequestException
import logging

# Logging ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = "7806413438:AAGao-5vJdpxxydutLHE_tl6rSIFm9MUeb4"
TOKEN_CONTRACT = "EGmrt3JKU1go9qJf28cedB8XnDzFnYAwe8LSgaQ7pump"
CHAT_ID = os.getenv('CHAT_ID', '-1001234567890')
ADMIN_IDS = os.getenv('ADMIN_IDS', '').split(',')
WEBSITE_URL = "https://atesin-kanatlari.onrender.com/"
TWITTER_URL = "https://x.com/ZetharaOfficial"
CMC_API_KEY = "40f5055b-a7a8-43d3-bf6a-92a9850e0467"
CMC_API_URL = "https://pro-api.coinmarketcap.com/v1"

# Global statistics
stats = {
    'total_transactions': 0,
    'total_volume': 0,
    'largest_transaction': 0
}

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome function for new members"""
    if update.message and update.message.new_chat_members:
        for new_member in update.message.new_chat_members:
            keyboard = [
                [
                    InlineKeyboardButton("Website 🌐", url=WEBSITE_URL),
                    InlineKeyboardButton("Twitter 🐦", url=TWITTER_URL)
                ],
                [InlineKeyboardButton("Token Info ℹ️", callback_data='token_info')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            welcome_message = await update.message.reply_text(
                f"🎉 Welcome {new_member.first_name}!\n"
                f"Thank you for joining our group!\n"
                f"Check out our links below:",
                reply_markup=reply_markup
            )
            await asyncio.sleep(30)
            await welcome_message.delete()

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    if query.data == 'token_info':
        await query.answer()
        info_text = (
            "🪙 Token Information:\n"
            "Name: Zethara Token\n"  # Token adınızı buraya ekleyin
            f"Contract: {TOKEN_CONTRACT[:6]}...{TOKEN_CONTRACT[-4:]}\n"
            "Network: Solana\n"
            f"Total Transactions: {stats['total_transactions']}\n"
            f"Total Volume: {stats['total_volume']:.2f}\n"
            f"Largest Transaction: {stats['largest_transaction']:.2f}"
        )
        await query.message.reply_text(info_text)

async def fetch_cmc_data(limit: int = 100) -> List[Dict]:
    """Fetch cryptocurrency data from CoinMarketCap API"""
    try:
        session = requests.Session()
        session.headers.update({
            'X-CMC_PRO_API_KEY': CMC_API_KEY,
            'Accept': 'application/json'
        })
        
        params = {
            'start': '1',
            'limit': str(limit),
            'convert': 'USD'
        }
        
        response = session.get(f"{CMC_API_URL}/cryptocurrency/listings/latest", params=params)
        data = response.json()
        
        if response.status_code == 200:
            return data.get('data', [])
        return []
        
    except RequestException as e:
        print(f"Error fetching CMC data: {e}")
        return []

async def top_coins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to show top cryptocurrency information"""
    await update.message.reply_text("🔄 Fetching top 100 cryptocurrencies from CoinMarketCap...")
    
    coins = await fetch_cmc_data()
    if not coins:
        await update.message.reply_text("❌ Failed to fetch cryptocurrency data.")
        return

    messages = []
    current_message = "📊 Top 100 Cryptocurrencies (CoinMarketCap)\n\n"
    
    for i, coin in enumerate(coins, 1):
        quote = coin['quote']['USD']
        coin_info = (
            f"{i}. {coin['symbol']} (${quote['price']:,.2f})\n"
            f"   24h: {quote['percent_change_24h']:+.2f}% "
            f"7d: {quote['percent_change_7d']:+.2f}%\n"
            f"   Vol 24h: ${quote['volume_24h']:,.0f} "
            f"Cap: ${quote['market_cap']:,.0f}\n"
        )
        
        if len(current_message) + len(coin_info) > 4000:
            messages.append(current_message)
            current_message = ""
        
        current_message += coin_info
    
    if current_message:
        messages.append(current_message)
    
    for msg in messages:
        await update.message.reply_text(msg)

async def coin_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get detailed information about a specific coin"""
    if not context.args:
        await update.message.reply_text("❌ Please specify a coin symbol. Example: /coin BTC")
        return
    
    symbol = context.args[0].upper()
    coins = await fetch_cmc_data(5000)
    
    coin = next((c for c in coins if c['symbol'].upper() == symbol), None)
    if not coin:
        await update.message.reply_text(f"❌ Coin {symbol} not found.")
        return
    
    quote = coin['quote']['USD']
    info = (
        f"💰 {coin['name']} ({coin['symbol']})\n\n"
        f"Rank: #{coin['cmc_rank']}\n"
        f"Price: ${quote['price']:,.8f}\n"
        f"Market Cap: ${quote['market_cap']:,.0f}\n"
        f"Volume 24h: ${quote['volume_24h']:,.0f}\n\n"
        f"Change:\n"
        f"1h: {quote['percent_change_1h']:+.2f}%\n"
        f"24h: {quote['percent_change_24h']:+.2f}%\n"
        f"7d: {quote['percent_change_7d']:+.2f}%\n"
        f"30d: {quote['percent_change_30d']:+.2f}%\n\n"
        f"Circulating Supply: {coin['circulating_supply']:,.0f} {coin['symbol']}\n"
        f"Total Supply: {coin['total_supply']:,.0f} {coin['symbol']}\n"
        f"Max Supply: {coin['max_supply']:,.0f} {coin['symbol'] if coin['max_supply'] else ''}"
    )
    
    keyboard = [[InlineKeyboardButton(
        "View on CoinMarketCap 🔍", 
        url=f"https://coinmarketcap.com/currencies/{coin['slug']}"
    )]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(info, reply_markup=reply_markup)

async def main():
    """Main function"""
    try:
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Add handlers
        application.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(CommandHandler("top100", top_coins_command))
        application.add_handler(CommandHandler("coin", coin_info_command))
        
        # Log başlangıç mesajı
        logger.info("Bot başlatılıyor...")
        
        # Start bot
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Bot çalışırken hata oluştu: {e}")
        raise e

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Kritik hata: {e}")
