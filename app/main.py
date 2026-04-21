import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

from .parser import parse_expense
from .sheets import save_to_sheet

# ---- Logging -----------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---- Config ------------------------------------------------------------------
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEB_DOMAIN = os.getenv("WEB_DOMAIN")

# ---- Lifespan ----------------------------------------------------------------
tg_app = Application.builder().token(TOKEN).build()


@asynccontextmanager
async def lifespan(application: FastAPI):
    # --- Startup ---
    # await tg_app.bot.set_webhook(url=f"{WEB_DOMAIN}/webhook")
    await tg_app.initialize()
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    await tg_app.start()
    logger.info("Bot started — webhook set to %s/webhook", WEB_DOMAIN)

    yield

    # --- Shutdown ---
    await tg_app.stop()
    await tg_app.shutdown()
    logger.info("Bot stopped gracefully.")


# ---- App ---------------------------------------------------------------------
app = FastAPI(lifespan=lifespan)


async def handle_msg(update: Update, context):
    text = update.message.text
    user_id = update.effective_user.id
    data = parse_expense(text)

    if data:
        try:
            await save_to_sheet(data, user_id)
            await update.message.reply_text(
                f"✅ Đã ghi: {data['item']} — {data['amount']:,.0f}đ"
            )
        except Exception:
            logger.exception("Lỗi xử lý tin nhắn user=%s", user_id)
            await update.message.reply_text("⚠️ Đã xảy ra lỗi, vui lòng thử lại.")
    else:
        await update.message.reply_text("❌ Sai định dạng (VD: Cafe 30k)")


@app.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"status": "ok", "message": "Finance Bot is running"}
