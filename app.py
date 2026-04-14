import asyncio
import sqlite3
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from aiohttp import web

# Настройки
API_TOKEN = '8654588828:AAEPpW0GHrS5HaPc_U-bvm2MevHxzBE5lbM'
PAY_TOKEN = 'ТУТ_ТОКЕН_ПЛАТЕЖКИ'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# БД
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, user_id INTEGER, item TEXT)')
    conn.commit()
    conn.close()

# Меню
PRICES = {
    "vip": {"title": "VIP", "price": 10000},
    "mega": {"title": "MEGA", "price": 18000}
}

@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    buttons = [[InlineKeyboardButton(text=f"{v['title']}", callback_data=f"buy_{k}")] for k, v in PRICES.items()]
    await message.answer("Магазин:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

# Заглушка для Render (чтобы он не выключал бота)
async def handle(request):
    return web.Response(text="Bot is alive")

async def main():
    init_db()
    # Запускаем веб-сервер на порту, который даст Render
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    # Запускаем и сервер, и бота одновременно
    await asyncio.gather(site.start(), dp.start_polling(bot))

if __name__ == '__main__':
    asyncio.run(main())
