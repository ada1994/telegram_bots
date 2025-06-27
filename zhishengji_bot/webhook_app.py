import os
import asyncio
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("TOKEN")

WELCOME_TEXT = (
    "您好，欢迎咨询直升机/机票/旅游业务。\n"
    "请直接联系客服 @Boatbabes，我们会第一时间为您服务！"
)

CONTACT_BUTTON = InlineKeyboardMarkup(
    [[InlineKeyboardButton("联系客服", url="https://t.me/Boatbabes")]]
)

ADMIN_ID = 7158664620  # 你的 Telegram 用户ID

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = (
        f"🆕 昵称: {user.full_name}\n"
        f"🆔 UserID: {user.id}\n"
        f"👤 Username: @{user.username if user.username else '无'}"
    )
    # 通知管理员
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
    except Exception as e:
        logging.error(f"通知管理员失败: {e}")

    # 回复客户欢迎消息
    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=CONTACT_BUTTON,
        parse_mode="HTML",
        disable_web_page_preview=True
    )

application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))

# 初始化 Telegram Application
main_loop = asyncio.new_event_loop()
asyncio.set_event_loop(main_loop)
main_loop.run_until_complete(application.initialize())

app = Flask(__name__)

@app.route("/", methods=["POST"])
def webhook():
    update_json = request.get_json(force=True)
    update = Update.de_json(update_json, application.bot)
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(application.process_update(update))
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "Bot is running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))