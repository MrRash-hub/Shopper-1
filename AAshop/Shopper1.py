import json
import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, JobQueue

# === Logging Setup ===
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === Config ===
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
CONFIG_FILE = "config.json"

# === Config Load/Save ===
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"interval_hours": 1}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

# === /start Command ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Bot aktif!\n\nGuna:\n"
        "/post – Hantar promosi sekarang\n"
        "/setup_post – Aktifkan auto-post ikut config\n"
        "/set_interval <jam> – Tukar selang masa (contoh: /set_interval 2)"
    )

# === Hantar Mesej ===
async def post(context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("⏰ Memulakan auto-post...")
    products = [
        {"title": "🛍️ Produk 1: Cordless Blower", "link": "https://shorturl.at/gtxRn"},
        {"title": "🛍️ Produk 2: Car Road Sign", "link": "https://shorturl.at/MRxbP"},
        {"title": "🛍️ Produk 3: Car side Mirror View", "link": "https://shorturl.at/EbyJN"},
        {"title": "🛍️ Produk 4: Universal Car Trash", "link": "https://shorturl.at/YpPsp"},
    ]
    for product in products:
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=f"{product['title']}\n{product['link']}")
            logger.info(f"✅ Hantar: {product['title']}")
        except Exception as e:
            logger.error(f"❌ Gagal hantar {product['title']}: {e}")

# === /post – Manual Hantar ===
async def manual_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔁 Menghantar promosi...")
    await post(context)
    await update.message.reply_text("✅ Promosi dihantar!")

# === /setup_post – Guna config.json ===
async def setup_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_config()
    hours = config.get("interval_hours", 1)
    interval = hours * 3600

    job_queue: JobQueue = context.job_queue
    job = job_queue.run_repeating(post, interval=interval, first=0)
    context.chat_data["job"] = job

    logger.info(f"🛠️ Auto-post diaktifkan setiap {hours} jam.")
    await update.message.reply_text(f"✅ Auto-post setiap {hours} jam telah diaktifkan.")

# === /set_interval <jam> ===
async def set_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("❌ Format salah. Guna: /set_interval <jam>")
        return

    hours = int(context.args[0])
    if hours < 1:
        await update.message.reply_text("❌ Minimum 1 jam diperlukan.")
        return

    save_config({"interval_hours": hours})

    old_job = context.chat_data.get("job")
    if old_job:
        old_job.schedule_removal()

    job_queue: JobQueue = context.job_queue
    new_job = job_queue.run_repeating(post, interval=hours * 3600, first=0)
    context.chat_data["job"] = new_job

    logger.info(f"⏱️ Selang masa ditukar kepada {hours} jam.")
    await update.message.reply_text(f"✅ Selang masa auto-post ditetapkan kepada setiap {hours} jam.")

# === Bot Setup ===
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("setup_post", setup_job))
app.add_handler(CommandHandler("post", manual_post))
app.add_handler(CommandHandler("set_interval", set_interval))

# === Auto-Mula Job bila bot hidup ===
config = load_config()
interval = config.get("interval_hours", 1) * 3600
job = app.job_queue.run_repeating(post, interval=interval, first=0)
logger.info(f"🚀 Bot dimulakan. Auto-post setiap {config['interval_hours']} jam.")

# === Mula polling ===
app.run_polling()

