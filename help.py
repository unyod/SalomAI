"""Help handler."""
from aiogram import F, Router
from aiogram.types import Message

router = Router()

HELP_TEXT = """
ℹ️ <b>Yordam</b>

<b>Asosiy buyruqlar:</b>
/start — Botni qayta ishga tushirish
/admin — Admin panel (faqat adminlar uchun)

<b>Funksiyalar:</b>
💬 <b>Yangi chat</b> — Yangi AI suhbat boshlash
📚 <b>Chatlarim</b> — Barcha chatlarni ko'rish va boshqarish
🧠 <b>Memory</b> — Uzoq muddatli xotirani boshqarish
📊 <b>Statistika</b> — Foydalanish statistikasi
⚙️ <b>Sozlamalar</b> — Bot sozlamalari

<b>Chat ichida:</b>
• Har qanday matnni yuboring — AI javob beradi
• «🛑 Chatni tugatish» — Chatni yakunlash

<b>Memory tizimi:</b>
Bot muhim ma'lumotlarni eslab qoladi va 
keyingi suhbatlarda ulardan foydalanadi.

<b>AI modellari:</b>
• Gemini — Google AI
• OpenAI — ChatGPT

Muammolar uchun admin bilan bog'laning.
"""


@router.message(F.text == "ℹ️ Yordam")
async def help_handler(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode="HTML")
