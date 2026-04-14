import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

PRICES = {
    "vip": {
        "title": "VIP", 
        "price": "100 ₽", 
        "desc": "• Домов: 7\n• Префикс: [VIP]\n• Команды: /kit vip, цветной ник\n• Кит: Золотое яблоко ×2, Алмаз ×8, Изумруд ×8, Бутылочка опыта ×32, Стейк ×16, Золотой слиток ×16, Лодка"
    },
    "mega": {
        "title": "MEGA", 
        "price": "180 ₽", 
        "desc": "• Домов: 10\n• Префикс: [MEGA]\n• Приоритет входа: Есть\n• Команды: /enderchest, /kit mega\n• Кит: Золотое яблоко ×4, Алмаз ×16, Изумруд ×16, Бутылочка опыта ×64, Стейк ×32, Золотой слиток ×32, Жемчуг Края ×8"
    },
    "ultra": {
        "title": "ULTRA", 
        "price": "400 ₽", 
        "desc": "• Домов: 100\n• Префикс: [ULTRA]\n• Приоритет входа: Есть\n• Команды: /enderchest, /anvil, /head, /kit ultra, телепорт без кулдауна\n• Кит: Зачарованное золотое яблоко ×1, Алмазный блок ×4, Изумрудный блок ×4, Бутылочка опыта ×128, Стейк ×64, Золотой блок ×8, Жемчуг Края ×16, Панцирь шалкера ×4"
    },
    "cosmo": {
        "title": "COSMO", 
        "price": "800 ₽", 
        "desc": "• Домов: 110\n• Префикс: [COSMO]\n• Приоритет входа: Есть\n• Команды: /enderchest, /anvil, /head, /kit cosmo, телепорт без кулдауна\n• Кит: Зачарованное золотое яблоко ×2, Алмазный блок ×8, Изумрудный блок ×8, Бутылочка опыта ×256, Стейк ×128, Золотой блок ×16, Жемчуг Края ×32, Панцирь шалкера ×8, Незеритовый скрап ×2"
    }
}

@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    buttons = [[InlineKeyboardButton(text=f"{v['title']} — {v['price']}", callback_data=f"buy_{k}")] for k, v in PRICES.items()]
    await message.answer("🛒 **Магазин VanillaLand**\nВыберите привилегию:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith('buy_'))
async def process_buy(callback: types.CallbackQuery):
    code = callback.data.split('_')[1]
    item = PRICES[code]
    text = f"💎 **{item['title']}**\n\n{item['desc']}\n\n💰 **Цена: {item['price']}**\n\nДля покупки напишите овнеру и нажмите кнопку ниже."
    buttons = [
        [InlineKeyboardButton(text="💬 Написать @Happy_Cucumber", url="https://t.me/Happy_Cucumber")],
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"check_{code}")]
    ]
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@dp.callback_query(F.data.startswith('check_'))
async def check_pay(callback: types.CallbackQuery):
    code = callback.data.split('_')[1]
    user = callback.from_user
    try:
        await bot.send_message(ADMIN_ID, f"🔔 **Новая заявка!**\nТовар: {PRICES[code]['title']}\nИгрок: @{user.username if user.username else 'id' + str(user.id)}\nID: `{user.id}`")
        await callback.message.answer("🚀 Заявка отправлена!")
    except:
        await callback.message.answer("❌ Ошибка уведомления овнера.")
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
