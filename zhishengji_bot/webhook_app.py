import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用直升机预定机器人！")

TOKEN = os.environ.get("TOKEN")
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))

app = Flask(__name__)

@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.process_update(update)  # 关键改动
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "Bot is running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))