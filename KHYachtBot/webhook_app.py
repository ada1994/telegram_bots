from flask import Flask, request
import os
from telegram import Update
from telegram.ext import Application, CommandHandler

TOKEN = os.environ.get("TOKEN")
application = Application.builder().token(TOKEN).build()

# 你的 start handler 代码...

app = Flask(__name__)

@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.process_update(update)
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return "Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))