import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 123456789  # ЗАМЕНИ на свой ID (узнай в @userinfobot), чтобы получать уведомления

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Все 4 привилегии
PRICES = {
    "vip": {"title": "VIP", "price": "100₽", "desc": "Домов: 7, Префикс [VIP]"},
    "mega": {"title": "MEGA", "price": "180₽", "desc": "Домов: 10, Префикс [MEGA]"},
    "ultra": {"title": "ULTRA", "price": "400₽", "desc": "Домов: 100, Префикс [ULTRA]"},
    "cosmo": {"title": "COSMO", "price": "800₽", "desc": "Домов: 110, Префикс [COSMO]"}
}

@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    buttons = [[InlineKeyboardButton(text=f"{v['title']} — {v['price']}", callback_data=f"buy_{k}")] for k, v in PRICES.items()]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("🛒 **Магазин доната VanillaLand**\n\nВыберите нужную привилегию:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith('buy_'))
async def process_buy(callback: types.CallbackQuery):
    code = callback.data.split('_')[1]
    item = PRICES[code]
    
    # Текст инструкции (можешь поменять под себя)
    text = (
        f"💳 **Покупка {item['title']}**\n\n"
        f"Цена: {item['price']}\n"
        f"Особенности: {item['desc']}\n\n"
        "Для оплаты напишите администратору или воспользуйтесь картой.\n"
        "После оплаты нажмите кнопку ниже."
    )
    
    # Кнопки: ссылка на оплату и проверка
    buttons = [
        [InlineKeyboardButton(text="Написать админу", url="https://t.me/твой_юзернейм")],
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"check_{code}")]
    ]
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith('check_'))
async def check_pay(callback: types.CallbackQuery):
    code = callback.data.split('_')[1]
    # Уведомление админу
    await bot.send_message(ADMIN_ID, f"🔔 **Заявка на покупку!**\nЮзер: @{callback.from_user.username}\nID: `{callback.from_user.id}`\nТовар: {code}")
    
    await callback.message.answer("Заявка отправлена! Админ проверит оплату и выдаст донат.")
    await callback.answer()

# Пингер для Render
async def handle(request):
    return web.Response(text="Bot is running")

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
