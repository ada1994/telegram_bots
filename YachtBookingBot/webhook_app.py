import os
import asyncio
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# 启用日志记录
logging.basicConfig(level=logging.INFO)

# 游艇信息字典
yacht_sizes = {
    "🚤 👉游艇推荐 More yachts": "https://t.me/youtingbaby/166", 
    "🏠👉 酒店推荐 /（旅行社代登记入住） ": "https://t.me/youtingbaby/345", 
    "💃👉 游艇宝贝 DJ Baby": "http://t.me/YachtDJ", 
}

ADMIN_ID = 7158664620  # 你的 Telegram 用户ID

# 底部大菜单
reply_keyboard = [
    ["⛵️游艇价格", "🏠酒店预定", "💃游艇宝贝"],
    ["🪪护照签证", "🚁直升机", "🚗接机租车"],
    ["🪪驾驶证办理", "🚤快艇包接送"]
]
reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Received /start command")
    user = update.effective_user

    # 1. 先发底部菜单
    await update.message.reply_text(
        "了解其他服务，请点击底部菜单选择：",
        reply_markup=reply_markup
    )

    # 2. 再发游艇信息采集（InlineKeyboard）
    keyboard = [
        [InlineKeyboardButton(size, url=url) for size, url in list(yacht_sizes.items())[i:i+1]]
        for i in range(0, len(yacht_sizes), 1)
    ]
    keyboard.append([InlineKeyboardButton("✈ 联系客服 Cust Serv", url='https://t.me/Boatbabes')])
    inline_markup = InlineKeyboardMarkup(keyboard)

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
        "📩 预订请点击菜单或联系人工客服 👉 @Boatbabes"
    )
    await update.message.reply_text(
        message_text,
        reply_markup=inline_markup,
        parse_mode="HTML",
        disable_web_page_preview=True
    )

    # 通知管理员
    msg = (
        f"🆕 昵称: {user.full_name}\n"
        f"🆔 UserID: {user.id}\n"
        f"👤 Username: @{user.username if user.username else '无'}"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
    except Exception as e:
        logging.error(f"通知管理员失败: {e}")

async def book_now_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("请发送您的联系方式和需求，我们会有专人联系您！")

def get_menu_links():
    return {
        "⛵️游艇价格": {
            "text": "⛵️ <b>游艇价格</b>\n点击下方链接查看更多游艇套餐详情：",
            "url": "https://t.me/youtingbaby/348"
        },
        "🏠酒店预定": {
            "text": "🏠 <b>酒店预定</b>\n查看推荐酒店及套餐：",
            "url": "https://t.me/youtingbaby/345"
        },
        "💃游艇宝贝": {
            "text": "💃 <b>游艇宝贝</b>\n西港DJ宝贝与派对活动：",
            "url": "https://t.me/YachtDJ"
        },
        "🪪护照签证": {
            "text": "🪪 <b>护照签证</b>\n办理护照/签证服务详情：",
            "url": "https://t.me/youtingbaby/134"
        },
        "🚁直升机": {
            "text": "🚁 <b>直升机服务</b>\n包机/观光服务介绍：",
            "url": "https://t.me/youtingbaby/139"
        },
        "🚗接机租车": {
            "text": "🚗 <b>接机租车</b>\n机场接送/包车服务：",
            "url": "https://t.me/youtingbaby/138"
        },
        "🪪驾驶证办理": {
            "text": "🪪 <b>驾驶证办理</b>\n柬埔寨/国际驾照服务：",
            "url": "https://t.me/youtingbaby/135"
        },
        "🚤快艇包接送": {
            "text": "🚤 <b>快艇包接送</b>\n快艇接送、上岛服务：",
            "url": "https://t.me/youtingbaby/114"
        }
    }

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip().replace(' ', '').lower()
    menu_links = get_menu_links()
    matched = None
    for key in menu_links:
        # 关键词模糊匹配，忽略空格和大小写
        if key.replace(' ', '').lower() in user_input or user_input in key.replace(' ', '').lower():
            matched = menu_links[key]
            break
    if matched:
        await update.message.reply_text(
            f"{matched['text']}\n<a href='{matched['url']}'>点击查看图文详情</a>",
            parse_mode="HTML",
            disable_web_page_preview=False
        )
    else:
        await update.message.reply_text("请选择底部菜单中的功能，或输入 /start 返回主菜单。", reply_markup=reply_markup)

# Telegram bot 初始化
TOKEN = os.environ.get("TOKEN")
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(book_now_callback, pattern='^book_now$'))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))

# 初始化 Telegram Application
main_loop = asyncio.new_event_loop()
asyncio.set_event_loop(main_loop)
main_loop.run_until_complete(application.initialize())

# Flask app
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