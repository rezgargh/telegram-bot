import os
import asyncio
import requests
from bs4 import BeautifulSoup
import jdatetime

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# =========================
# CONFIG
# =========================
import os

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("anylashop")  # مثلا: @anilashop

if not TOKEN:
    raise Exception("BOT_TOKEN is missing in environment variables")

if not CHANNEL_ID:
    raise Exception("CHANNEL_ID is missing in environment variables")


# =========================
# EXTRACT IMAGE FROM LINK
# =========================
def extract_image(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # بهترین عکس (OG image)
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]

        # fallback: اولین تصویر
        img = soup.find("img")
        if img and img.get("src"):
            return img["src"]

        return None
    except:
        return None


# =========================
# CONVERT DATE (MILADI → JALALI)
# =========================
def convert_expiry(day_number):
    try:
        today = jdatetime.date.today()
        expiry = today.replace(day=int(day_number))
        return expiry.strftime("%Y/%m/%d")
    except:
        return "نامشخص"


# =========================
# START COMMAND
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📦 لینک محصول را ارسال کن\n"
        "بعد قیمت و تخفیف را وارد کن"
    )


# =========================
# MAIN LOGIC
# =========================
user_data = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    text = update.message.text

    # STEP 1: LINK
    if text.startswith("http"):
        user_data[user_id] = {"link": text}
        await update.message.reply_text("💰 قیمت محصول را وارد کن:")
        return

    # STEP 2: PRICE
    if user_id in user_data and "price" not in user_data[user_id]:
        user_data[user_id]["price"] = text
        await update.message.reply_text("🎯 تخفیف را وارد کن (مثلا 10):")
        return

    # STEP 3: DISCOUNT + FINAL POST
    if user_id in user_data and "discount" not in user_data[user_id]:
        user_data[user_id]["discount"] = text

        data = user_data[user_id]

        link = data["link"]
        price = float(data["price"])
        discount = float(data["discount"])

        final_price = price - (price * discount / 100)

        image = extract_image(link)
        expiry = convert_expiry(22)

        caption = f"""
🛍 محصول جدید

💰 قیمت اصلی: ${price}
🔥 قیمت بعد تخفیف: ${final_price}

📅 تاریخ انقضا: {expiry}
"""

        try:
            if image:
                await context.bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=image,
                    caption=caption
                )
            else:
                await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=caption
                )

            await update.message.reply_text("✅ محصول ارسال شد")

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

        user_data.pop(user_id)
        return


# =========================
# MAIN RUNNER (IMPORTANT FOR RENDER)
# =========================
async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")

    await app.run_polling()


import os

if __name__ == "__main__":
    print("Bot is running...")
    app.run_polling()
