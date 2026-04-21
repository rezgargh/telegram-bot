import os
import requests
from bs4 import BeautifulSoup
import jdatetime
from datetime import datetime

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters


import os

print("TOKEN:", os.environ.get("BOT_TOKEN"))
print("CHANNEL:", os.environ.get("anylashop"))
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("anylashop")


# -------------------------
# product extractor
# -------------------------
def extract_product(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        name = soup.find("meta", property="og:title")
        name = name["content"] if name else "Product"

        image = soup.find("meta", property="og:image")
        image = image["content"] if image else None

        return name, image

    except:
        return "Product", None


# -------------------------
# Jalali date
# -------------------------
def to_jalali(day):
    today = datetime.now()
    try:
        g = datetime(today.year, today.month, int(day))
    except:
        g = today

    return jdatetime.date.fromgregorian(date=g).strftime("%Y/%m/%d")


# -------------------------
# start
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send: URL | PRICE | DISCOUNT | DAY")


# -------------------------
# handler
# -------------------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        url, price, discount, day = [x.strip() for x in text.split("|")]

        final_price = int(price) - int(discount)

        name, img = extract_product(url)
        date = to_jalali(day)

        caption = f"""
🛍 {name}

💰 Price: ${final_price}

📅 Expiry: {date}
"""

        if img:
            await context.bot.send_photo(CHANNEL_ID, img, caption=caption)
        else:
            await context.bot.send_message(CHANNEL_ID, caption)

        await update.message.reply_text("✅ Posted!")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


# -------------------------
# main (SAFE for Render)
# -------------------------
def main():
    if not TOKEN:
        print("❌ BOT_TOKEN missing")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🤖 Bot running...")

    try:
        app.run_polling(drop_pending_updates=True)
    except RuntimeError:
        import nest_asyncio
        nest_asyncio.apply()
        app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
