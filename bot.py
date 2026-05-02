import os
import re
import aiohttp
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ---------- Flask HTTP server (keeps Render alive) ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "Terabox Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ---------- Telegram bot ----------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
COOKIE = os.environ.get("COOKIE")

def get_surl(url):
    match = re.search(r'(?:surl=|/s/)([a-zA-Z0-9_-]+)', url)
    return match.group(1) if match else None

async def get_video(url):
    surl = get_surl(url)
    if not surl:
        return None
    
    api = f"https://www.terabox.app/share/list?app_id=250528&shorturl={surl}&root=1"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Cookie': f'ndus={COOKIE}'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(api, headers=headers, timeout=30) as resp:
            data = await resp.json()
            if data.get('list'):
                return data['list'][0].get('dlink')
    return None

async def start(update, context):
    await update.message.reply_text("Send me a Terabox link")

async def handle(update, context):
    text = update.message.text
    if 'terabox' not in text.lower():
        return
    
    await update.message.reply_text("Processing...")
    link = await get_video(text)
    
    if link:
        await update.message.reply_text(f"✅ {link}")
    else:
        await update.message.reply_text("❌ Failed")

def run_bot():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set")
        return
    if not COOKIE:
        print("❌ COOKIE not set")
        return
    
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    
    print("✅ Bot started!")
    bot_app.run_polling()

# ---------- Main ----------
if __name__ == "__main__":
    # Start Flask in background thread
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("✅ Flask server running on port", os.environ.get("PORT", 10000))
    
    # Start bot in main thread
    run_bot()
