import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 读取 TOKEN
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

def main():
    if not TOKEN:
        print("请设置 TOKEN 环境变量")
        return
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == "__main__":
    main()
