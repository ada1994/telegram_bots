import os
import asyncio
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import re
import json
MENU_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'menu_config.json')

# 加载菜单栏按钮配置
def load_menu_config():
    try:
        with open(MENU_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"buttons": []}

def save_menu_config(config):
    with open(MENU_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_custom_keyboard():
    config = load_menu_config()
    buttons = config.get('buttons', [])
    keyboard = []
    # 每2个按钮一行
    for i in range(0, len(buttons), 2):
        row = []
        for btn in buttons[i:i+2]:
            row.append(InlineKeyboardButton(btn['text'], url=btn['url']))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard) if keyboard else None


# 启用日志记录
logging.basicConfig(level=logging.INFO)

# 游艇信息字典
yacht_sizes = {
    "🚤 游艇推荐 More yachts": "https://t.me/youtingbaby/166",
    "💃 游艇宝贝 DJ Baby": "http://t.me/YachtDJ", 
    "🏠 酒店推荐（旅行社代登记入住）": "https://t.me/youtingbaby/345"
}

ADMIN_ID = 7158664620  # 你的 Telegram 用户ID

# 底部大菜单
reply_keyboard = [
    ["⛵️游艇价格", "🏠酒店预定", "💃游艇宝贝"],
    ["🪪护照签证", "🚁直升机", "🚗接机租车"],
    ["🪪驾驶证办理", "🚤快艇包接送"]
]
reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

# 广告关键词过滤
AD_KEYWORDS = [
    r"http[s]?://", r"t\.me/", r"tg://", r"微信", r"VX", r"加群", r"推广", r"广告", r"QQ", r"@[a-zA-Z0-9_]{4,}"
]

# 敏感行业词监控关键词
SENSITIVE_KEYWORDS = [
    "游艇价格", "包船", "西港游艇", "高龙岛酒店", "酒店", "直升机", "海钓", "签证", "劳工证", "驾照", "护照", "游艇", "上岛", "皇家", "机票",
    "多少", "费用", "情人岛", "天堂岛", "撒冷岛", "游艇宝贝", "DJ", "多少钱", "什么价格", "费用"
]

async def is_owner(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status == 'creator'
    except Exception as e:
        logging.error(f"获取用户身份失败: {e}")
        return False

async def auto_delete_message(bot, chat_id, message_id, delay=300):
    try:
        await asyncio.sleep(delay)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logging.error(f"自动删除消息失败: {e}")

async def filter_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    # 检查是否包含广告关键词
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in AD_KEYWORDS):
        try:
            await update.message.delete()
            # 回复警告消息
            warn_msg = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                reply_to_message_id=update.message.message_id,
                text="检测到广告，已删除。"
            )
            # 5分钟后自动删除警告
            asyncio.create_task(auto_delete_message(context.bot, warn_msg.chat_id, warn_msg.message_id, 120))
        except Exception as e:
            logging.error(f"广告处理失败: {e}")
    else:
        # 非广告消息，群成员自动删除逻辑
        chat = update.effective_chat
        user = update.effective_user
        # 只在群聊中生效
        if chat.type in ["group", "supergroup"]:
            try:
                member = await context.bot.get_chat_member(chat.id, user.id)
                if member.status not in ["administrator", "creator"]:
                    # 2分钟后自动删除普通成员消息
                    asyncio.create_task(auto_delete_message(context.bot, chat.id, update.message.message_id, 120))
            except Exception as e:
                logging.error(f"自动删除群成员消息失败: {e}")

# 敏感词监控：只通知管理员，不群内提示
async def monitor_sensitive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").replace(' ', '').lower()
    if any(word.lower() in text for word in SENSITIVE_KEYWORDS):
        try:
            msg = (
                f"⚠️ 监控到敏感词\n"
                f"群: {update.effective_chat.title or update.effective_chat.id}\n"
                f"用户: {update.effective_user.full_name} (@{update.effective_user.username or '无'})\n"
                f"内容: {update.message.text or ''}"
            )
            admin_msg = await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
            asyncio.create_task(auto_delete_message(context.bot, ADMIN_ID, admin_msg.message_id, 120))
        except Exception as e:
            logging.error(f"敏感词监控失败: {e}")

# --- 管理菜单相关命令，仅管理员可用 ---
async def set_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "菜单管理命令：\n"
        "/add_button 名称 链接  —— 添加按钮\n"
        "/edit_button 序号 新名称 新链接  —— 修改按钮\n"
        "/remove_button 序号  —— 删除按钮\n"
        "/show_menu  —— 查看当前菜单栏\n"
        "最多支持4个按钮。"
    )

async def add_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("用法：/add_button 名称 链接")
        return
    try:
        name, url = ' '.join(context.args[:-1]), context.args[-1]
    except Exception:
        await update.message.reply_text("参数解析失败，请检查格式。")
        return
    config = load_menu_config()
    buttons = config.get('buttons', [])
    if len(buttons) >= 4:
        await update.message.reply_text("最多只能有4个按钮！")
        return
    buttons.append({"text": name, "url": url})
    config['buttons'] = buttons
    save_menu_config(config)
    await update.message.reply_text(f"已添加按钮：{name} -> {url}")
    await update.message.reply_text(f"[DEBUG] 当前按钮配置: {json.dumps(config, ensure_ascii=False)}")

async def edit_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 3:
        await update.message.reply_text("用法：/edit_button 序号 新名称 新链接")
        return
    try:
        idx = int(context.args[0]) - 1
        name = ' '.join(context.args[1:-1])
        url = context.args[-1]
    except Exception:
        await update.message.reply_text("参数解析失败，请检查格式。")
        return
    config = load_menu_config()
    buttons = config.get('buttons', [])
    if idx < 0 or idx >= len(buttons):
        await update.message.reply_text("序号超出范围！")
        return
    buttons[idx] = {"text": name, "url": url}
    config['buttons'] = buttons
    save_menu_config(config)
    await update.message.reply_text(f"已修改第{idx+1}个按钮为：{name} -> {url}")
    await update.message.reply_text(f"[DEBUG] 当前按钮配置: {json.dumps(config, ensure_ascii=False)}")

async def remove_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 1:
        await update.message.reply_text("用法：/remove_button 序号")
        return
    idx = context.args[0]
    try:
        idx = int(idx) - 1
    except Exception:
        await update.message.reply_text("序号必须为数字（从1开始）")
        return
    config = load_menu_config()
    buttons = config.get('buttons', [])
    if idx < 0 or idx >= len(buttons):
        await update.message.reply_text("序号超出范围！")
        return
    btn = buttons.pop(idx)
    config['buttons'] = buttons
    save_menu_config(config)
    await update.message.reply_text(f"已删除按钮：{btn['text']}")
    await update.message.reply_text(f"[DEBUG] 当前按钮配置: {json.dumps(config, ensure_ascii=False)}")

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    config = load_menu_config()
    buttons = config.get('buttons', [])
    if not buttons:
        await update.message.reply_text("当前没有设置任何按钮。")
        return
    msg = '\n'.join([f"{i+1}. {b['text']} -> {b['url']}" for i, b in enumerate(buttons)])
    await update.message.reply_text(f"当前菜单栏按钮：\n{msg}")

# --- 管理员专属：动态推送目标和带菜单栏 ---
admin_post_targets = {}  # user_id -> target_id

async def post_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("用法：/post_to <群组或频道ID>")
        return
    target_id = context.args[0]
    admin_post_targets[update.effective_user.id] = target_id
    await update.message.reply_text(f"本次推送目标已设置为：{target_id}\n请发送图片+文字，机器人会自动推送到目标。")

async def admin_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    photo_file = update.message.photo[-1].file_id
    caption = update.message.caption or ""
    reply_markup = get_custom_keyboard()
    target_id = admin_post_targets.pop(update.effective_user.id, None)
    if target_id:
        try:
            await context.bot.send_photo(
                chat_id=target_id,
                photo=photo_file,
                caption=caption,
                reply_markup=reply_markup
            )
            await update.message.reply_text(f"已推送到 {target_id}，如需再次推送请重新设置目标。")
        except Exception as e:
            await update.message.reply_text(f"推送失败：{e}")
    else:
        await context.bot.send_photo(
            chat_id=update.effective_user.id,
            photo=photo_file,
            caption=caption,
            reply_markup=reply_markup
        )
        await update.message.reply_text("已生成带菜单栏的图文消息，可手动转发到频道/群组。\n如需机器人主动推送，请先用 /post_to <目标ID> 设置目标。")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Received /start command")
    user = update.effective_user

    # 1. 先发底部菜单
    menu_msg = await update.message.reply_text(
        "了解其他服务，请点击底部菜单选择：",
        reply_markup=reply_markup
    )
    # 只有非 owner 才自动删除机器人消息和用户消息
    if not await is_owner(context.bot, update.message.chat_id, update.effective_user.id):
        asyncio.create_task(auto_delete_message(context.bot, menu_msg.chat_id, menu_msg.message_id, 120))
        asyncio.create_task(auto_delete_message(context.bot, update.message.chat_id, update.message.message_id, 120))

    # 2. 再发游艇信息采集（InlineKeyboard）
    keyboard = [
        [InlineKeyboardButton(size, url=url) for size, url in list(yacht_sizes.items())[i:i+2]]
        for i in range(0, len(yacht_sizes), 2)
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
        "⏰ 常规出海时间：09:00 – 18:00\n"
        "📍 航线：西港码头 – 高龙岛 / 撒冷岛\n"
        "Route: Koh Rong / Koh Rong Sanloem\n"
        "📲 支持中文 & English 服务\n\n"
        "🎉 <b>自费服务内容：</b>\n"
        "DJ宝贝｜水上项目｜深潜浮潜｜摩托艇｜山地车｜岛上食宿\n"
        "Boat Babes | Water Sports | Diving & Snorkeling | Jet Ski | ATV | Island Stay & Meals\n\n"
        "📩 预订请点击菜单或联系人工客服 👉 @Boatbabes"
    )
    info_msg = await update.message.reply_text(
        message_text,
        reply_markup=inline_markup,
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    if not await is_owner(context.bot, update.message.chat_id, update.effective_user.id):
        asyncio.create_task(auto_delete_message(context.bot, info_msg.chat_id, info_msg.message_id, 120))

    # 通知管理员
    msg = (
        f"🆕 昵称: {user.full_name}\n"
        f"🆔 UserID: {user.id}\n"
        f"👤 Username: @{user.username if user.username else '无'}"
    )
    try:
        admin_msg = await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
        asyncio.create_task(auto_delete_message(context.bot, ADMIN_ID, admin_msg.message_id, 120))
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
        menu_msg = await update.message.reply_text(
            f"{matched['text']}\n<a href='{matched['url']}'>点击查看图文详情</a>",
            parse_mode="HTML",
            disable_web_page_preview=False
        )
        if not await is_owner(context.bot, update.message.chat_id, update.effective_user.id):
            asyncio.create_task(auto_delete_message(context.bot, menu_msg.chat_id, menu_msg.message_id, 120))
    else:
        menu_msg = await update.message.reply_text("请选择底部菜单中的功能，或输入 /start 返回主菜单。", reply_markup=reply_markup)
        if not await is_owner(context.bot, update.message.chat_id, update.effective_user.id):
            asyncio.create_task(auto_delete_message(context.bot, menu_msg.chat_id, menu_msg.message_id, 120))
    # 删除用户的原始消息（非 owner）
    if not await is_owner(context.bot, update.message.chat_id, update.effective_user.id):
        asyncio.create_task(auto_delete_message(context.bot, update.message.chat_id, update.message.message_id, 120))

# Telegram bot 初始化
TOKEN = os.environ.get("TOKEN")
application = Application.builder().token(TOKEN).build()
# 管理员专属菜单命令
application.add_handler(CommandHandler("set_menu", set_menu))
application.add_handler(CommandHandler("add_button", add_button))
application.add_handler(CommandHandler("edit_button", edit_button))
application.add_handler(CommandHandler("remove_button", remove_button))
application.add_handler(CommandHandler("show_menu", show_menu))
# 管理员专属：通过用户ID直接联系用户
async def contact_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("无权限")
        return
    if len(context.args) < 2:
        await update.message.reply_text("用法：/contact_id <用户ID> <消息内容>")
        return
    try:
        user_id = int(context.args[0])
        msg = ' '.join(context.args[1:])
        await context.bot.send_message(chat_id=user_id, text=msg)
        await update.message.reply_text(f"已发送消息给 {user_id}")
    except Exception as e:
        await update.message.reply_text(f"发送失败：{e}")
application.add_handler(CommandHandler("contact_id", contact_id))
# 管理员专属：动态推送目标命令
application.add_handler(CommandHandler("post_to", post_to))
# 管理员专属：图片+文字自动带菜单栏/推送
application.add_handler(MessageHandler(filters.PHOTO & filters.User(user_id=ADMIN_ID), admin_photo_handler))

# 优先处理广告过滤
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_ads), group=0)
# 敏感词监控（只通知管理员）
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor_sensitive), group=1)
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(book_now_callback, pattern='^book_now$'))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu), group=2)

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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))io.set_event_loop(main_loop)
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