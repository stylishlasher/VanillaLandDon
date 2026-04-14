import asyncio
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
    asyncio.run(main())
