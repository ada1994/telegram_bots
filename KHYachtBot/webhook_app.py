import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用 KHYachtBot！")  # 其它机器人可自定义

TOKEN = os.environ.get("TOKEN")
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))

# --- 关键：模块加载时就初始化 Telegram Application ---
loop = asyncio.get_event_loop()
loop.run_until_complete(application.initialize())

app = Flask(__name__)

@app.route("/", methods=["POST"])
def webhook():
    update_json = request.get_json(force=True)
    update = Update.de_json(update_json, application.bot)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(application.process_update(update))
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "Bot is running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))