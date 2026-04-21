import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from datetime import datetime
import jdatetime

from flask import Flask
from threading import Thread

TOKEN = "8621161135:AAEI5bpvgHCDfMdHHJViV5-288prdeClY_8"
CHANNEL_ID = "@AnylaShop"

LINK, NAME, PRICE, DISCOUNT, DATE = range(5)

# ---------------- KEEP ALIVE SERVER ----------------
web_app = Flask('')

@web_app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    web_app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# ---------------- IMAGE SCRAPER ----------------
def get_best_image(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]

        imgs = []
        for img in soup.find_all("img"):
            src = img.get("src")
            if src and "http" in src:
                imgs.append(src)

        return imgs[0] if imgs else None

    except:
        return None

# ---------------- DATE CONVERT ----------------
def convert_date(day):
    now = datetime.now()
    g = datetime(now.year, now.month, day)
    j = jdatetime.date.fromgregorian(date=g)
    return j.strftime("%Y/%m/%d")

# ---------------- BOT FLOW ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔗 لینک محصول رو بفرست:")
    return LINK

async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    context.user_data["link"] = url
    context.user_data["image"] = get_best_image(url)

    await update.message.reply_text("📝 نام محصول:")
    return NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("💰 قیمت (USD):")
    return PRICE

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["price"] = float(update.message.text)
    await update.message.reply_text("🎯 تخفیف (%):")
    return DISCOUNT

async def discount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["discount"] = float(update.message.text)
    await update.message.reply_text("📅 روز ماه (مثلاً 22):")
    return DATE

async def date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = int(update.message.text)
    jalali = convert_date(day)

    name = context.user_data["name"]
    price = context.user_data["price"]
    discount = context.user_data["discount"]
    img = context.user_data["image"]

    final = price - (price * discount / 100)

    text = f"""
🛍 {name}

💰 قیمت: ${price}
🔥 قیمت نهایی: ${final:.2f}

📅 انقضا: {jalali}
"""

    if img:
        await context.bot.send_photo(CHANNEL_ID, img, caption=text)
    else:
        await context.bot.send_message(CHANNEL_ID, text)

    await update.message.reply_text("✅ ارسال شد")
    return ConversationHandler.END

# ---------------- RUN BOT ----------------
def main():
    keep_alive()

    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LINK: [MessageHandler(filters.TEXT, link)],
            NAME: [MessageHandler(filters.TEXT, name)],
            PRICE: [MessageHandler(filters.TEXT, price)],
            DISCOUNT: [MessageHandler(filters.TEXT, discount)],
            DATE: [MessageHandler(filters.TEXT, date)],
        },
        fallbacks=[]
    )

    app.add_handler(conv)

    print("🤖 Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()