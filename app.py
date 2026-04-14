import asyncio
import os
import logging
import time
from datetime import datetime
from collections import defaultdict
from typing import Dict, Optional

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiohttp import web

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
SERVER_IP = os.getenv('SERVER_IP', 'ваш_сервер_ip')
RCON_PORT = int(os.getenv('RCON_PORT', 25575))
RCON_PASSWORD = os.getenv('RCON_PASSWORD')

if not API_TOKEN or not ADMIN_ID:
    raise ValueError("BOT_TOKEN и ADMIN_ID должны быть заданы")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

PRICES = {
    "vip": {
        "title": "VIP",
        "price": "100 ₽",
        "price_num": 100,
        "desc": "• Домов: 7\n• Префикс: [VIP]\n• Команды: /kit vip, цветной ник\n• Кит: Золотое яблоко ×2, Алмаз ×8, Изумруд ×8, Бутылочка опыта ×32, Стейк ×16, Золотой слиток ×16, Лодка",
        "minecraft_command": "lp user {username} parent add vip"
    },
    "mega": {
        "title": "MEGA",
        "price": "180 ₽",
        "price_num": 180,
        "desc": "• Домов: 10\n• Префикс: [MEGA]\n• Приоритет входа: Есть\n• Команды: /enderchest, /kit mega\n• Кит: Золотое яблоко ×4, Алмаз ×16, Изумруд ×16, Бутылочка опыта ×64, Стейк ×32, Золотой слиток ×32, Жемчуг Края ×8",
        "minecraft_command": "lp user {username} parent add mega"
    },
    "ultra": {
        "title": "ULTRA",
        "price": "400 ₽",
        "price_num": 400,
        "desc": "• Домов: 100\n• Префикс: [ULTRA]\n• Приоритет входа: Есть\n• Команды: /enderchest, /anvil, /head, /kit ultra, телепорт без кулдауна\n• Кит: Зачарованное золотое яблоко ×1, Алмазный блок ×4, Изумрудный блок ×4, Бутылочка опыта ×128, Стейк ×64, Золотой блок ×8, Жемчуг Края ×16, Панцирь шалкера ×4",
        "minecraft_command": "lp user {username} parent add ultra"
    },
    "cosmo": {
        "title": "COSMO",
        "price": "800 ₽",
        "price_num": 800,
        "desc": "• Домов: 110\n• Префикс: [COSMO]\n• Приоритет входа: Есть\n• Команды: /enderchest, /anvil, /head, /kit cosmo, телепорт без кулдауна\n• Кит: Зачарованное золотое яблоко ×2, Алмазный блок ×8, Изумрудный блок ×8, Бутылочка опыта ×256, Стейк ×128, Золотой блок ×16, Жемчуг Края ×32, Панцирь шалкера ×8, Незеритовый скрап ×2",
        "minecraft_command": "lp user {username} parent add cosmo"
    }
}

user_cooldown = defaultdict(float)
pending_payments = {}

class MinecraftRCON:
    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.port = port
        self.password = password
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            logger.info(f"Подключено к RCON {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Ошибка RCON: {e}")
            return False

    async def send_command(self, command: str) -> str:
        if not self.writer:
            await self.connect()
        try:
            self.writer.write(f"{command}\n".encode())
            await self.writer.drain()
            response = await self.reader.read(1024)
            return response.decode().strip()
        except Exception as e:
            logger.error(f"Ошибка отправки {command}: {e}")
            return ""

    async def execute_command(self, command: str) -> bool:
        response = await self.send_command(command)
        success = "error" not in response.lower()
        if success:
            logger.info(f"✅ Команда выполнена: {command}")
        else:
            logger.error(f"❌ Ошибка выполнения: {command} - {response}")
        return success

rcon = MinecraftRCON(SERVER_IP, RCON_PORT, RCON_PASSWORD) if RCON_PASSWORD else None

async def notify_admin(text: str):
    try:
        await bot.send_message(ADMIN_ID, text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка уведомления админа: {e}")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    buttons = [[InlineKeyboardButton(text=f"{v['title']} — {v['price']}", callback_data=f"buy_{k}")] for k, v in PRICES.items()]
    buttons.append([InlineKeyboardButton(text="📜 Мои покупки", callback_data="my_purchases")])
    await message.answer("🛒 **Магазин VanillaLand**\n\nВыберите привилегию:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = "📖 Помощь по командам:\n\n/start - Магазин\n/info - О сервере\n/help - Помощь\n/mypurchases - Покупки"
    await message.answer(help_text, parse_mode="Markdown")

@dp.message(Command("info"))
async def cmd_info(message: types.Message):
    info_text = "🎮 VanillaLand Server\n\n📌 IP: mc.vanillaland.ru\n📌 Версия: 1.20.4"
    await message.answer(info_text, parse_mode="Markdown")

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await cmd_start(callback.message)
    await callback.answer()

@dp.callback_query(F.data.startswith('buy_'))
async def process_buy(callback: types.CallbackQuery):
    code = callback.data.split('_')[1]
    item = PRICES[code]
    text = f"💎 **{item['title']}**\n\n{item['desc']}\n\n💰 **Цена: {item['price']}**"
    buttons = [
        [InlineKeyboardButton(text="💬 Написать владельцу", url="https://t.me/Happy_Cucumber")],
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"payment_{code}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith('payment_'))
async def process_payment(callback: types.CallbackQuery):
    code = callback.data.split('_')[1]
    user_id = callback.from_user.id
    current_time = asyncio.get_event_loop().time()
    if current_time - user_cooldown[user_id] < 10:
        await callback.answer("⏳ Подождите 10 секунд", show_alert=True)
        return
    user_cooldown[user_id] = current_time
    pending_payments[user_id] = {"code": code, "username": None, "timestamp": datetime.now()}
    await callback.message.answer(f"🎮 **Отлично!**\nВы выбрали: {PRICES[code]['title']}\n\n📝 **Введите ваш никнейм в Minecraft:**")
    await notify_admin(f"🔔 **Заявка!**\nПользователь: @{callback.from_user.username}\nID: {user_id}\n💎: {PRICES[code]['title']}")
    await callback.answer()

@dp.message(F.text)
async def handle_username(message: types.Message):
    user_id = message.from_user.id
    if user_id not in pending_payments or message.text.startswith('/'):
        return
    username = message.text.strip()
    if not username or len(username) > 16 or not username.replace("_", "").isalnum():
        await message.answer("❌ Неверный формат никнейма!")
        return
    payment_info = pending_payments[user_id]
    payment_info["username"] = username
    code = payment_info["code"]
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin_confirm_{user_id}_{code}_{username}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_deny_{user_id}")]
    ])
    await bot.send_message(ADMIN_ID, f"💰 **ЗАЯВКА**\nИгрок: `{username}`\n💎: {PRICES[code]['title']}\nID: `{user_id}`", parse_mode="Markdown", reply_markup=admin_keyboard)
    await message.answer(f"✅ **Заявка отправлена!**\nНик: `{username}`\nОжидайте подтверждения.")

@dp.callback_query(F.data.startswith("admin_confirm_"))
async def admin_confirm_callback(callback: types.CallbackQuery):
    if str(callback.from_user.id) != ADMIN_ID:
        return
    parts = callback.data.split('_')
    user_id, code, username = int(parts[2]), parts[3], parts[4]
    if rcon:
        command = PRICES[code]["minecraft_command"].format(username=username)
        if await rcon.execute_command(command):
            await bot.send_message(user_id, f"🎉 **Успешно!**\nПривилегия {PRICES[code]['title']} выдана!")
            await callback.message.edit_text(f"✅ Выдано {username}")
        else:
            await callback.message.edit_text(f"❌ Ошибка RCON. Команда: {command}")
    else:
        await callback.message.edit_text(f"⚠️ RCON OFF. Выдай сам: {PRICES[code]['minecraft_command'].format(username=username)}")
    if user_id in pending_payments: del pending_payments[user_id]
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_deny_"))
async def admin_deny_callback(callback: types.CallbackQuery):
    user_id = int(callback.data.split('_')[2])
    await bot.send_message(user_id, "❌ Ваша заявка отклонена.")
    if user_id in pending_payments: del pending_payments[user_id]
    await callback.message.edit_text("❌ Отклонено.")
    await callback.answer()

async def handle(request):
    return web.Response(text="VanillaLand Bot is running!")

async def main():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    if rcon: await rcon.connect()
    await notify_admin("✅ Бот запущен!")
    try:
        await asyncio.gather(site.start(), dp.start_polling(bot))
    finally:
        if rcon and rcon.writer:
            rcon.writer.close()
            await rcon.writer.wait_closed()
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        passimport asyncio
import os
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

API_TOKEN = os.getenv('BOT_TOKEN')
try:
    ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
except ValueError:
    ADMIN_ID = 0

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
user_spam_check = {}

PRICES = {
    "vip": {
        "title": "VIP", "price": "100 ₽", 
        "desc": "• Домов: 7\n• Префикс: [VIP]\n• Команды: /kit vip, цветной ник\n• Кит: Золотое яблоко ×2, Алмаз ×8, Изумруд ×8, Стейк ×16"
    },
    "mega": {
        "title": "MEGA", "price": "180 ₽", 
        "desc": "• Домов: 10\n• Префикс: [MEGA]\n• Приоритет входа: Есть\n• Команды: /enderchest, /kit mega"
    },
    "ultra": {
        "title": "ULTRA", "price": "400 ₽", 
        "desc": "• Домов: 100\n• Префикс: [ULTRA]\n• Команды: /enderchest, /anvil, /head, /kit ultra"
    },
    "cosmo": {
        "title": "COSMO", "price": "800 ₽", 
        "desc": "• Домов: 110\n• Префикс: [COSMO]\n• /gm 1, /near, телепорт без кулдауна"
    }
}

def get_main_menu():
    buttons = [[InlineKeyboardButton(text=f"{v['title']} — {v['price']}", callback_data=f"buy_{k}")] for k, v in PRICES.items()]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer("🛒 **Магазин VanillaLand**\nВыберите привилегию:", reply_markup=get_main_menu())

@dp.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text("🛒 **Магазин VanillaLand**\nВыберите привилегию:", reply_markup=get_main_menu())
    await callback.answer()

@dp.callback_query(F.data.startswith('buy_'))
async def process_buy(callback: types.CallbackQuery):
    code = callback.data.split('_')[1]
    item = PRICES[code]
    text = f"💎 **{item['title']}**\n\n{item['desc']}\n\n💰 **Цена: {item['price']}**\n\nДля покупки напишите овнеру:"
    buttons = [
        [InlineKeyboardButton(text="💬 Написать @Happy_Cucumber", url="https://t.me/Happy_Cucumber")],
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"check_{code}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="to_main")]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith('check_'))
async def check_pay(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    current_time = time.time()
    
    if user_id in user_spam_check and current_time - user_spam_check[user_id] < 10:
        await callback.answer("⏳ Не спамьте! Подождите 10 секунд.", show_alert=True)
        return

    user_spam_check[user_id] = current_time
    code = callback.data.split('_')[1]
    user = callback.from_user
    
    try:
        await bot.send_message(ADMIN_ID, f"🔔 **Новая заявка!**\nТовар: {PRICES[code]['title']}\nИгрок: @{user.username if user.username else 'id' + str(user.id)}\nID: `{user.id}`")
        await callback.message.answer("🚀 Заявка отправлена овнеру!")
    except:
        await callback.message.answer("❌ Ошибка уведомления. Напишите напрямую @Happy_Cucumber")
    await callback.answer()

async def handle(request):
    return web.Response(text="VanillaLand Bot is running!")

async def main():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await asyncio.gather(site.start(), dp.start_polling(bot))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
