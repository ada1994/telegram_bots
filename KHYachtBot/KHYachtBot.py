import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler

# 启用日志记录
logging.basicConfig(level=logging.DEBUG)

# 设置游艇信息字典
yacht_sizes = {
    "38ft 双体快艇👨‍👩‍👧‍👦20人": "https://t.me/youtingbaby/122", 
    "39ft 快艇Speedboat👨‍👩‍👧‍👦20人": "https://t.me/youtingbaby/115", 
    "39ft 钓鱼艇 ‍👩‍👧‍👦12人": "https://t.me/youtingbaby/109", 
    "42ft 双体Yacht👨‍👩‍👧‍👦10人": "https://t.me/youtingbaby/40?single", 
    "42ft 德宏Yacht👨‍👩‍👧‍👦12人": "https://t.me/youtingbaby/71", 
    "54ft Azimut👨‍👩‍👧‍👦15人": "https://t.me/youtingbaby/30",
    "62ft 星瑞Sease‍👩‍👧‍👦19人": "https://t.me/youtingbaby/107",
    "63ft Sea-Stella👨‍👩‍👧‍👦19人": "https://t.me/youtingbaby/102",
    "63ft JF游艇👨‍👩‍👧‍👦20人": "https://t.me/youtingbaby/158",
    "65ft JP👨‍👩‍👧‍👦19人": "https://t.me/youtingbaby/89",
    "95尺 ZH游艇👨‍👩‍👧‍👦50人": "https://t.me/youtingbaby/150",
    "95ft 水神Aquitalia👨‍👩‍👧‍👦50人": "https://t.me/youtingbaby/69"
}

async def start(update: Update, context):
    logging.debug("Received /start command")

    # 创建每排两个按钮的布局
    keyboard = [
        [InlineKeyboardButton(size, url=url) for size, url in list(yacht_sizes.items())[i:i+2]]
        for i in range(0, len(yacht_sizes), 2)
    ]
    keyboard.append([InlineKeyboardButton("✈ 联系客服 Cust Serv", url='https://t.me/Boatbabes')])
    keyboard.append([InlineKeyboardButton("📅 在线预订", callback_data='book_now')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = (
        "🤖 <b>西港游艇服务</b>\n"
        "Sihanoukville Yacht Booking\n\n"
        "🛥 提供豪华游艇租赁服务，42尺至95尺可选\n"
        "Luxury yacht rentals from 42ft to 95ft\n\n"
        "🚤 <b>游艇尺寸 & 载客限制</b>\n\n"
        "<a href='https://t.me/youtingbaby/28'>DJ宝贝定制服务</a>\n"
        "<a href='https://t.me/youtingbaby/122'>38ft快艇Speedboat👨‍👩‍👧‍👦20人</a>\n"
        "<a href='https://t.me/youtingbaby/115'>39ft快艇Speedboat👨‍👩‍👧‍👦20人 350$/趟</a>\n"
        "<a href='https://t.me/youtingbaby/109'>39ft钓鱼艇Fishing Boat👨‍👩‍👧‍👦12人 1000$起</a>\n"
        "<a href='https://t.me/youtingbaby/40?single'>42ft双体游艇👨‍👩‍👧‍👦12人 $1280</a>\n"
        "<a href='https://t.me/youtingbaby/71'>42ft德宏‍👩‍👧‍👦10人 1600$</a>\n"
        "<a href='https://t.me/youtingbaby/30'>54ft 意大利Azimut👨‍👩‍👧‍👦15人 1800$</a>\n"
        "<a href='https://t.me/youtingbaby/107'>62ft 星瑞Sease👨‍👩‍👧‍👦19人 2800$</a>\n"
        "<a href='https://t.me/youtingbaby/102'>63ft Sea-Stella👨‍👩‍👧‍👦19人 2500$</a>\n"
        "<a href='https://t.me/youtingbaby/158'>63ft JF游艇👨‍👩‍👧‍👦20人 2200$</a>\n"
        "<a href='https://t.me/youtingbaby/89'>65ft JP游艇👨‍👩‍👧‍👦19人 2600$</a>\n"
        "<a href='https://t.me/youtingbaby/69'>95ft 水神Aquitalia👨‍👩‍👧‍👦50人 4500$</a>\n"
        "<a href='https://t.me/youtingbaby/150'>95ft ZH忠恒👨‍👩‍👧‍50人 5500$</a>\n\n"
        "⏰ 出海时间：09:00 – 17:00\n"
        "📍 航线：西港码头 – 高龙岛 / 撒冷岛\n"
        "Route: Koh Rong / Koh Rong Sanloem\n"
        "📲 支持中文 & English 服务\n\n"
        "🎉 <b>自费服务内容：</b>\n"
        "DJ宝贝｜水上项目｜深潜浮潜｜摩托艇｜山地车｜岛上食宿\n"
        "Boat Babes | Water Sports | Diving & Snorkeling | Jet Ski | ATV | Island Stay & Meals\n\n"
        "📩 预订请点击菜单或联系人工客服 👉 @Boatbabes\n"
        "Click the menu or contact live support 👉 @Boatbabes"
    )

    # ====== 通知管理员 ======
    user = update.effective_user
    msg = (
        f"🆕 Новый пользователь: {user.full_name}\n"
        f"🆔 UserID: {user.id}\n"
        f"👤 Username: @{user.username if user.username else '无'}"
    )
    admin_id = 7158664620  # 你的 Telegram 用户ID
    try:
        await context.bot.send_message(chat_id=admin_id, text=msg)
    except Exception as e:
        logging.error(f"通知管理员失败: {e}")

    # ====== 给客户回复欢迎消息 ======
    await update.message.reply_text(
        message_text,
        reply_markup=reply_markup,
        parse_mode="HTML",
        disable_web_page_preview=True
    )

def main():
    TOKEN = os.environ.get("TOKEN")
    if not TOKEN:
        print("请设置 TOKEN 环境变量")
        return
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == "__main__":
    main()
