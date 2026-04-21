import requests
from bs4 import BeautifulSoup
from telegram import Update, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from datetime import datetime
import jdatetime

TOKEN = "8621161135:AAEI5bpvgHCDfMdHHJViV5-288prdeClY_8"
CHANNEL_ID = "@AnylaShop"  # آیدی کانالت

# مراحل گفتگو
LINK, NAME, PRICE, DISCOUNT, DATE = range(5)

# -----------------------------
# استخراج بهترین عکس
# -----------------------------
def get_best_image(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        images = []

        # og:image (بهترین حالت)
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]

        # img tag ها
        for img in soup.find_all("img"):
            src = img.get("src")
            if src and ("http" in src):
                images.append(src)

        # فیلتر عکس‌های کوچک یا لوگو
        filtered = [img for img in images if not any(x in img.lower() for x in ["logo", "icon", "banner"])]

        if filtered:
            return filtered[0]

        return None

    except Exception as e:
        print("❌ Image error:", e)
        return None

# -----------------------------
# تبدیل تاریخ میلادی به شمسی
# -----------------------------
def convert_to_jalali(day):
    now = datetime.now()
    g_date = datetime(now.year, now.month, day)
    j_date = jdatetime.date.fromgregorian(date=g_date)
    return j_date.strftime("%Y/%m/%d")

# -----------------------------
# شروع
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔗 لینک محصول رو بفرست:")
    return LINK

# -----------------------------
async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    context.user_data["link"] = url

    image = get_best_image(url)
    context.user_data["image"] = image

    await update.message.reply_text("📝 نام محصول رو وارد کن:")
    return NAME

# -----------------------------
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("💰 قیمت اصلی (به دلار) رو وارد کن:")
    return PRICE

# -----------------------------
async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["price"] = float(update.message.text)
    await update.message.reply_text("🎯 درصد تخفیف رو وارد کن (مثلاً 20):")
    return DISCOUNT

# -----------------------------
async def get_discount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["discount"] = float(update.message.text)
    await update.message.reply_text("📅 روز ماه میلادی رو وارد کن (مثلاً 22):")
    return DATE

# -----------------------------
async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        day = int(update.message.text)
        jalali_date = convert_to_jalali(day)

        name = context.user_data["name"]
        price = context.user_data["price"]
        discount = context.user_data["discount"]
        image = context.user_data["image"]

        final_price = price - (price * discount / 100)

        caption = f"""
🛍 {name}

💰 قیمت اصلی: ${price}
🔥 قیمت بعد تخفیف: ${round(final_price,2)}

📅 تاریخ انقضا: {jalali_date}
"""

        # ارسال به کانال
        if image:
            await context.bot.send_photo(chat_id=CHANNEL_ID, photo=image, caption=caption)
        else:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=caption)

        await update.message.reply_text("✅ محصول با موفقیت در کانال ارسال شد")

        return ConversationHandler.END

    except Exception as e:
        await update.message.reply_text("❌ خطا در تاریخ، دوباره وارد کن")
        return DATE

# -----------------------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ لغو شد")
    return ConversationHandler.END

# -----------------------------
# اجرای ربات
# -----------------------------
app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link)],
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
        DISCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_discount)],
        DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(conv_handler)

print("🤖 Bot is running...")
app.run_polling(drop_pending_updates=True)